from typing import Dict, List

import numpy as np
import torch
from scipy import ndimage


def pixel_metrics_from_logits(logits: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> Dict[str, float]:
    """
    像素级辅助指标，用于训练日志观察；不作为论文中的 Pd/Fa 定义。
    """
    prob = torch.sigmoid(logits)
    pred = (prob >= threshold).float()
    target = (target >= 0.5).float()

    tp = (pred * target).sum().item()
    fp = (pred * (1 - target)).sum().item()
    fn = ((1 - pred) * target).sum().item()
    tn = ((1 - pred) * (1 - target)).sum().item()

    precision = tp / (tp + fp + 1e-6)
    recall = tp / (tp + fn + 1e-6)
    iou = tp / (tp + fp + fn + 1e-6)
    dice = 2 * tp / (2 * tp + fp + fn + 1e-6)
    acc = (tp + tn) / (tp + tn + fp + fn + 1e-6)

    return {'precision': precision, 'recall': recall, 'iou': iou, 'dice': dice, 'acc': acc}


def _square_structure(radius: int) -> np.ndarray:
    radius = int(max(radius, 0))
    return np.ones((2 * radius + 1, 2 * radius + 1), dtype=bool)


def dtum_metrics_single(
    pred_mask: np.ndarray,
    gt_mask: np.ndarray,
    detect_radius: int = 1,
    fa_radius: int = 4,
) -> Dict[str, float]:
    """
    按 DTUM / Shooting Rules 风格计算单张图的目标检出数和虚警像素数。

    Pd:
      对 GT mask 做 8 连通域标记，每个连通域视为一个真实目标。
      如果预测 mask 在该 GT 连通域的 detect_radius 邻域内有任意像素，则该目标被检出。
      默认 detect_radius=1，对应 3x3 容差。

    Fa:
      在 GT 目标周围 fa_radius 邻域内的预测像素不计入虚警。
      保护区外的所有预测前景像素计为 false-alarm pixels。
      默认 fa_radius=4，对应 9x9 保护区域。
    """
    pred = np.asarray(pred_mask) > 0
    gt = np.asarray(gt_mask) > 0
    if pred.shape != gt.shape:
        raise ValueError(f'pred shape {pred.shape} != gt shape {gt.shape}')

    conn8 = np.ones((3, 3), dtype=bool)
    gt_lab, gt_num = ndimage.label(gt, structure=conn8)

    detected = 0
    det_struct = _square_structure(detect_radius)
    for gid in range(1, gt_num + 1):
        gt_comp = gt_lab == gid
        if detect_radius > 0:
            hit_region = ndimage.binary_dilation(gt_comp, structure=det_struct)
        else:
            hit_region = gt_comp
        if np.any(pred[hit_region]):
            detected += 1

    if fa_radius > 0 and np.any(gt):
        protect_region = ndimage.binary_dilation(gt, structure=_square_structure(fa_radius))
    else:
        protect_region = gt

    false_alarm_pixels = int(np.logical_and(pred, ~protect_region).sum())
    total_pixels = int(gt.size)

    pd = float(detected / gt_num) if gt_num > 0 else 0.0
    fa = float(false_alarm_pixels / max(total_pixels, 1))

    return {
        'pd': pd,
        'fa': fa,
        'fa_pixel_rate': fa,
        'detected_targets': int(detected),
        'total_targets': int(gt_num),
        'false_alarm_pixels': int(false_alarm_pixels),
        'total_pixels': int(total_pixels),
    }


def dtum_metrics_per_sample_from_logits(
    logits: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    detect_radius: int = 1,
    fa_radius: int = 4,
) -> List[Dict[str, float]]:
    prob = torch.sigmoid(logits)
    pred = (prob >= threshold).float().detach().cpu().numpy()
    gt = (target >= 0.5).float().detach().cpu().numpy()

    out = []
    for i in range(pred.shape[0]):
        out.append(dtum_metrics_single(pred[i, 0], gt[i, 0], detect_radius=detect_radius, fa_radius=fa_radius))
    return out


def dtum_metrics_from_logits(
    logits: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    detect_radius: int = 1,
    fa_radius: int = 4,
) -> Dict[str, float]:
    per_sample = dtum_metrics_per_sample_from_logits(
        logits, target, threshold=threshold, detect_radius=detect_radius, fa_radius=fa_radius
    )

    detected = sum(int(x['detected_targets']) for x in per_sample)
    total_targets = sum(int(x['total_targets']) for x in per_sample)
    false_alarm_pixels = sum(int(x['false_alarm_pixels']) for x in per_sample)
    total_pixels = sum(int(x['total_pixels']) for x in per_sample)

    pd = float(detected / total_targets) if total_targets > 0 else 0.0
    fa = float(false_alarm_pixels / max(total_pixels, 1))

    return {
        'pd': pd,
        'fa': fa,
        'fa_pixel_rate': fa,
        'fa_per_image': fa,  # 兼容旧字段名；当前含义为像素虚警率。
        'detected_targets': int(detected),
        'total_targets': int(total_targets),
        'false_alarm_pixels': int(false_alarm_pixels),
        'total_pixels': int(total_pixels),
    }


target_metrics_per_sample_from_logits = dtum_metrics_per_sample_from_logits
target_metrics_from_logits = dtum_metrics_from_logits
