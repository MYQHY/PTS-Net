import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from datasets.pmrk_dataset import PMRKDataset, pmrk_collate_fn
from models.pts_main_aux_net import PTSMainAuxNet
from utils.io import set_seed, split_sequences, collect_samples, read_sequence_list
from utils.losses import DualHeadLoss
from utils.metrics import pixel_metrics_from_logits, target_metrics_from_logits, target_metrics_per_sample_from_logits
from utils.model_info import get_model_size_info


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', type=str, required=True)
    parser.add_argument('--save_dir', type=str, required=True)
    parser.add_argument('--epochs', type=int, default=60)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--lr_step_size', type=int, default=20, help='StepLR 阶梯衰减周期；<=0 表示关闭。')
    parser.add_argument('--lr_gamma', type=float, default=0.5, help='StepLR 每次衰减倍率。')
    parser.add_argument('--img_size', type=int, default=0, help='>0 时强制 resize 为正方形；0 表示保持原尺寸并动态 padding。')
    parser.add_argument('--train_ratio', type=float, default=0.8)
    parser.add_argument('--train_txt', type=str, default=None)
    parser.add_argument('--val_txt', type=str, default=None)
    parser.add_argument('--num_workers', type=int, default=0)
    parser.add_argument('--base_ch', type=int, default=32)
    parser.add_argument('--aux_scale', type=float, default=0.5, help='辅助分支 [H,C] 融合强度')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--threshold_latest', type=float, default=0.5)
    parser.add_argument('--threshold_traj', type=float, default=0.5)
    parser.add_argument('--grad_clip', type=float, default=1.0)
    parser.add_argument('--pd_radius', type=int, default=1, help='Pd 检测容差半径，1 表示 GT 周围 3x3 区域内命中即检出。')
    parser.add_argument('--fa_radius', type=int, default=4, help='Fa 保护区半径，4 表示 GT 周围 9x9 区域内预测不计虚警。')
    return parser.parse_args()


def save_sequence_metrics(sequence_stats, csv_path: Path, json_path: Path):
    rows = []
    for seq, rec in sorted(sequence_stats.items()):
        total_targets = int(rec['total_targets'])
        total_pixels = int(rec['total_pixels'])
        rows.append({
            'sequence': seq,
            'num_samples': int(rec['num_samples']),
            'pd': float(rec['detected_targets'] / total_targets) if total_targets > 0 else 0.0,
            'fa': float(rec['false_alarm_pixels'] / max(total_pixels, 1)),
            'detected_targets': int(rec['detected_targets']),
            'total_targets': total_targets,
            'false_alarm_pixels': int(rec['false_alarm_pixels']),
            'total_pixels': total_pixels,
        })

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'sequence', 'num_samples', 'pd', 'fa',
                'detected_targets', 'total_targets', 'false_alarm_pixels', 'total_pixels'
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    return rows


def run_one_epoch(
    model, loader, optimizer, criterion, device, thr_latest=0.5,
    train=True, grad_clip=0.0, pd_radius=1, fa_radius=4
):
    model.train() if train else model.eval()

    loss_sum = 0.0
    pixel_sum = {'precision': 0.0, 'recall': 0.0, 'iou': 0.0, 'dice': 0.0, 'acc': 0.0}
    count = 0

    detected_targets = 0
    total_targets = 0
    false_alarm_pixels = 0
    total_pixels = 0

    sequence_stats = defaultdict(lambda: {
        'detected_targets': 0,
        'total_targets': 0,
        'false_alarm_pixels': 0,
        'total_pixels': 0,
        'num_samples': 0,
    })

    pbar = tqdm(loader, leave=False)
    for batch in pbar:
        x, y_latest, y_traj, metas = batch
        x = x.to(device, non_blocking=True)
        y_latest = y_latest.to(device, non_blocking=True)
        y_traj = y_traj.to(device, non_blocking=True)

        if train:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(train):
            out = model(x)
            loss = criterion(out['latest'], y_latest, out['traj'], y_traj)
            if train:
                loss.backward()
                if grad_clip and grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)
                optimizer.step()

        pix = pixel_metrics_from_logits(out['latest'].detach(), y_latest, threshold=thr_latest)
        tgt = target_metrics_from_logits(
            out['latest'].detach(), y_latest, threshold=thr_latest,
            detect_radius=pd_radius, fa_radius=fa_radius
        )

        bs = x.shape[0]
        loss_sum += loss.item() * bs
        for k, v in pix.items():
            pixel_sum[k] += v * bs
        count += bs

        detected_targets += int(tgt['detected_targets'])
        total_targets += int(tgt['total_targets'])
        false_alarm_pixels += int(tgt['false_alarm_pixels'])
        total_pixels += int(tgt['total_pixels'])

        cur_pd = detected_targets / max(total_targets, 1)
        cur_fa = false_alarm_pixels / max(total_pixels, 1)
        pbar.set_description(f'loss={loss.item():.4f}, pd={cur_pd:.4f}, fa={cur_fa:.2e}')

        if not train:
            per_sample = target_metrics_per_sample_from_logits(
                out['latest'].detach(), y_latest, threshold=thr_latest,
                detect_radius=pd_radius, fa_radius=fa_radius
            )
            for meta, sm in zip(metas, per_sample):
                seq = meta['sequence']
                sequence_stats[seq]['detected_targets'] += int(sm['detected_targets'])
                sequence_stats[seq]['total_targets'] += int(sm['total_targets'])
                sequence_stats[seq]['false_alarm_pixels'] += int(sm['false_alarm_pixels'])
                sequence_stats[seq]['total_pixels'] += int(sm['total_pixels'])
                sequence_stats[seq]['num_samples'] += 1

    out_stats = {k: v / max(count, 1) for k, v in pixel_sum.items()}
    out_stats['loss'] = loss_sum / max(count, 1)
    out_stats['pd'] = float(detected_targets / total_targets) if total_targets > 0 else 0.0
    out_stats['fa'] = float(false_alarm_pixels / max(total_pixels, 1))
    out_stats['fa_pixel_rate'] = out_stats['fa']
    out_stats['fa_per_image'] = out_stats['fa']  # 兼容旧字段名；当前含义为像素虚警率。
    out_stats['detected_targets'] = int(detected_targets)
    out_stats['total_targets'] = int(total_targets)
    out_stats['false_alarm_pixels'] = int(false_alarm_pixels)
    out_stats['total_pixels'] = int(total_pixels)

    return out_stats, sequence_stats


def main():
    args = parse_args()
    set_seed(args.seed)

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    if args.train_txt and args.val_txt:
        train_seqs = read_sequence_list(args.train_txt)
        val_seqs = read_sequence_list(args.val_txt)
    else:
        train_seqs, val_seqs = split_sequences(args.data_root, args.train_ratio)

    train_samples = collect_samples(args.data_root, train_seqs, require_labels=True)
    val_samples = collect_samples(args.data_root, val_seqs, require_labels=True)

    if len(train_samples) == 0:
        raise RuntimeError('训练集为空，请检查 inputs/mask_latest/traj_mask 是否存在。')
    if len(val_samples) == 0:
        raise RuntimeError('验证集为空，请检查 train_ratio 或标签目录。')

    print(f'Train sequences: {train_seqs}')
    print(f'Val sequences: {val_seqs}')
    print(f'Train samples: {len(train_samples)}')
    print(f'Val samples: {len(val_samples)}')
    print(f'DTUM metrics: pd_radius={args.pd_radius}, fa_radius={args.fa_radius}')

    with open(save_dir / 'split.json', 'w', encoding='utf-8') as f:
        json.dump({'train_sequences': train_seqs, 'val_sequences': val_seqs}, f, ensure_ascii=False, indent=2)

    train_ds = PMRKDataset(train_samples, img_size=args.img_size, training=True)
    val_ds = PMRKDataset(val_samples, img_size=args.img_size, training=False)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=True, drop_last=False,
                              collate_fn=pmrk_collate_fn)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True, drop_last=False,
                            collate_fn=pmrk_collate_fn)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = PTSMainAuxNet(base_ch=args.base_ch, aux_scale=args.aux_scale).to(device)
    model_info = get_model_size_info(model)
    print('Model info:', model_info)
    with open(save_dir / 'model_info.json', 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)

    criterion = DualHeadLoss(lambda_latest=1.0, lambda_traj=0.6)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = None
    if args.lr_step_size is not None and args.lr_step_size > 0:
        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=args.lr_step_size, gamma=args.lr_gamma
        )
        print(f'StepLR enabled: step_size={args.lr_step_size}, gamma={args.lr_gamma}')

    best_pd = -1.0
    best_fa = float('inf')
    history = []

    for epoch in range(1, args.epochs + 1):
        train_stats, _ = run_one_epoch(
            model, train_loader, optimizer, criterion, device,
            thr_latest=args.threshold_latest, train=True, grad_clip=args.grad_clip,
            pd_radius=args.pd_radius, fa_radius=args.fa_radius
        )
        val_stats, val_sequence_stats = run_one_epoch(
            model, val_loader, optimizer, criterion, device,
            thr_latest=args.threshold_latest, train=False, grad_clip=0.0,
            pd_radius=args.pd_radius, fa_radius=args.fa_radius
        )

        current_lr = optimizer.param_groups[0]['lr']
        record = {'epoch': epoch, 'lr': current_lr, 'train': train_stats, 'val': val_stats}
        history.append(record)

        print(
            f"[Epoch {epoch:03d}] "
            f"lr={current_lr:.6e} "
            f"train_loss={train_stats['loss']:.4f} "
            f"val_loss={val_stats['loss']:.4f} "
            f"val_pd={val_stats['pd']:.4f} "
            f"val_fa={val_stats['fa']:.6e} "
            f"val_p={val_stats['precision']:.4f} "
            f"val_r={val_stats['recall']:.4f}"
        )

        seq_rows = save_sequence_metrics(
            val_sequence_stats,
            save_dir / f'val_sequence_metrics_epoch_{epoch:03d}.csv',
            save_dir / f'val_sequence_metrics_epoch_{epoch:03d}.json',
        )
        save_sequence_metrics(
            val_sequence_stats,
            save_dir / 'val_sequence_metrics_latest.csv',
            save_dir / 'val_sequence_metrics_latest.json',
        )
        for row in seq_rows:
            print(f"    {row['sequence']}: pd={row['pd']:.4f}, fa={row['fa']:.6e}, n={row['num_samples']}")

        with open(save_dir / 'history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        latest_path = save_dir / 'latest.pt'
        torch.save({
            'model': model.state_dict(),
            'epoch': epoch,
            'val': val_stats,
            'args': vars(args),
            'optimizer': optimizer.state_dict(),
            'scheduler': scheduler.state_dict() if scheduler is not None else None,
        }, latest_path)

        better = False
        if val_stats['pd'] > best_pd:
            better = True
        elif abs(val_stats['pd'] - best_pd) < 1e-12 and val_stats['fa'] < best_fa:
            better = True

        if better:
            best_pd = val_stats['pd']
            best_fa = val_stats['fa']
            best_path = save_dir / 'best.pt'
            torch.save({
                'model': model.state_dict(),
                'epoch': epoch,
                'val': val_stats,
                'args': vars(args),
                'optimizer': optimizer.state_dict(),
                'scheduler': scheduler.state_dict() if scheduler is not None else None,
            }, best_path)
            save_sequence_metrics(
                val_sequence_stats,
                save_dir / 'val_sequence_metrics_best.csv',
                save_dir / 'val_sequence_metrics_best.json',
            )
            print(f"  -> 保存 best.pt, val_pd={val_stats['pd']:.4f}, val_fa={val_stats['fa']:.6e}")

        if scheduler is not None:
            scheduler.step()


if __name__ == '__main__':
    main()
