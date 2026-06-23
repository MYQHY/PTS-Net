from pathlib import Path
from typing import Dict

import torch


def get_model_size_info(model: torch.nn.Module, ckpt_path: str = None) -> Dict[str, float]:
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    param_size_mb = total_params * 4 / (1024 ** 2)
    info = {
        'total_params': int(total_params),
        'trainable_params': int(trainable_params),
        'param_size_mb_fp32': float(param_size_mb),
    }

    pts_bank = getattr(model, 'pts_bank', None)
    if pts_bank is not None and hasattr(pts_bank, 'get_weight_table'):
        try:
            info['pts_bank_weights'] = pts_bank.get_weight_table()
        except Exception:
            pass

    if ckpt_path is not None and Path(ckpt_path).exists():
        info['checkpoint_size_mb'] = float(Path(ckpt_path).stat().st_size / (1024 ** 2))
    return info
