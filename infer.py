import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader

from datasets.pmrk_dataset import PMRKDataset, pmrk_collate_fn
from models.pts_main_aux_net import PTSMainAuxNet
from utils.io import collect_samples, read_sequence_list
from utils.model_info import get_model_size_info


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', type=str, required=True)
    parser.add_argument('--ckpt', type=str, required=True)
    parser.add_argument('--save_dir', type=str, required=True)
    parser.add_argument('--test_txt', type=str, default=None, help='测试序列列表 txt，每行一个 Sequence 名称。')
    parser.add_argument('--img_size', type=int, default=0, help='>0 时强制 resize 为正方形；0 表示保持原尺寸并动态 padding。')
    parser.add_argument('--batch_size', type=int, default=1)
    parser.add_argument('--num_workers', type=int, default=0)
    parser.add_argument('--base_ch', type=int, default=32)
    parser.add_argument('--aux_scale', type=float, default=0.5)
    parser.add_argument('--threshold_latest', type=float, default=0.5)
    parser.add_argument('--threshold_traj', type=float, default=0.5)
    parser.add_argument('--save_prob_png', type=int, default=1)
    parser.add_argument('--save_prob_npy', type=int, default=1)
    parser.add_argument('--warmup_iters', type=int, default=5)
    return parser.parse_args()


def save_mask(mask: np.ndarray, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((mask.astype(np.uint8) * 255)).save(path)


def save_prob_png(prob: np.ndarray, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.clip(prob, 0.0, 1.0)
    Image.fromarray((arr * 255.0).astype(np.uint8)).save(path)


def main():
    args = parse_args()

    sequences = read_sequence_list(args.test_txt) if args.test_txt else None
    samples = collect_samples(args.data_root, sequences=sequences, require_labels=False)
    ds = PMRKDataset(samples, img_size=args.img_size, training=False, return_meta=True)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers, pin_memory=True,
                        collate_fn=pmrk_collate_fn)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = PTSMainAuxNet(base_ch=args.base_ch, aux_scale=args.aux_scale).to(device)

    ckpt = torch.load(args.ckpt, map_location='cpu')
    model.load_state_dict(ckpt['model'])
    model.eval()

    model_info = get_model_size_info(model, args.ckpt)
    print('Model info:', model_info)

    save_root = Path(args.save_dir)
    save_root.mkdir(parents=True, exist_ok=True)
    with open(save_root / 'model_info.json', 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)

    warmup_done = 0
    with torch.no_grad():
        for batch in loader:
            x, _, _, _ = batch
            x = x.to(device, non_blocking=True)
            if device.type == 'cuda':
                torch.cuda.synchronize()
            _ = model(x)
            if device.type == 'cuda':
                torch.cuda.synchronize()
            warmup_done += 1
            if warmup_done >= args.warmup_iters:
                break

    total_forward_time = 0.0
    total_images = 0

    with torch.no_grad():
        for batch in loader:
            x, _, _, metas = batch
            x = x.to(device, non_blocking=True)

            if device.type == 'cuda':
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            out = model(x)
            prob_latest = torch.sigmoid(out['latest'])
            prob_traj = torch.sigmoid(out['traj'])
            if device.type == 'cuda':
                torch.cuda.synchronize()
            dt = time.perf_counter() - t0

            total_forward_time += dt
            total_images += x.shape[0]

            pred_latest = (prob_latest >= args.threshold_latest).float().cpu().numpy()
            pred_traj = (prob_traj >= args.threshold_traj).float().cpu().numpy()
            prob_latest_np = prob_latest.cpu().numpy()
            prob_traj_np = prob_traj.cpu().numpy()

            for i in range(x.shape[0]):
                meta = metas[i]
                seq = meta['sequence']
                latest_idx = int(meta['latest_idx'])
                in_h, in_w = meta['input_hw']
                name = f'{latest_idx:03d}.png'
                stem = f'{latest_idx:03d}'

                latest_mask = pred_latest[i, 0][:in_h, :in_w]
                traj_mask = pred_traj[i, 0][:in_h, :in_w]
                latest_prob = prob_latest_np[i, 0][:in_h, :in_w]
                traj_prob = prob_traj_np[i, 0][:in_h, :in_w]

                save_mask(latest_mask, save_root / seq / 'mask' / name)
                save_mask(traj_mask, save_root / seq / 'traj_mask' / name)

                if args.save_prob_png:
                    save_prob_png(latest_prob, save_root / seq / 'mask_prob' / name)
                    save_prob_png(traj_prob, save_root / seq / 'traj_prob' / name)
                if args.save_prob_npy:
                    (save_root / seq / 'mask_prob_npy').mkdir(parents=True, exist_ok=True)
                    (save_root / seq / 'traj_prob_npy').mkdir(parents=True, exist_ok=True)
                    np.save(save_root / seq / 'mask_prob_npy' / f'{stem}.npy', latest_prob.astype(np.float32))
                    np.save(save_root / seq / 'traj_prob_npy' / f'{stem}.npy', traj_prob.astype(np.float32))

    speed = {
        'num_images': int(total_images),
        'total_forward_time_sec': float(total_forward_time),
        'avg_forward_time_ms_per_image': float((total_forward_time / max(total_images, 1)) * 1000.0),
        'fps_forward_only': float(total_images / max(total_forward_time, 1e-12)),
        'device': str(device),
        'batch_size': int(args.batch_size),
    }
    print('Inference speed:', speed)
    with open(save_root / 'inference_speed.json', 'w', encoding='utf-8') as f:
        json.dump(speed, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
