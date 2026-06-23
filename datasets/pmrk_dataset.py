from typing import List, Dict, Optional, Tuple
import random

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset

from utils.io import load_input_mat, load_mask, parse_latest_idx_from_name


class PMRKDataset(Dataset):
    def __init__(self, samples: List[Dict[str, str]], img_size: int = 0, training: bool = True, return_meta: bool = False):
        self.samples = samples
        self.img_size = img_size
        self.training = training
        self.return_meta = return_meta

    def __len__(self):
        return len(self.samples)

    def _resize_if_needed(self, x: torch.Tensor) -> torch.Tensor:
        if self.img_size is None or self.img_size <= 0:
            return x
        return F.interpolate(x.unsqueeze(0), size=(self.img_size, self.img_size), mode='bilinear', align_corners=False).squeeze(0)

    def _resize_mask_if_needed(self, y: torch.Tensor) -> torch.Tensor:
        if self.img_size is None or self.img_size <= 0:
            return y
        return F.interpolate(y.unsqueeze(0), size=(self.img_size, self.img_size), mode='nearest').squeeze(0)

    def _augment(self, x: torch.Tensor, y1: Optional[torch.Tensor], y2: Optional[torch.Tensor]):
        if not self.training:
            return x, y1, y2

        if random.random() < 0.5:
            x = torch.flip(x, dims=[2])
            if y1 is not None:
                y1 = torch.flip(y1, dims=[2])
            if y2 is not None:
                y2 = torch.flip(y2, dims=[2])

        if random.random() < 0.5:
            x = torch.flip(x, dims=[1])
            if y1 is not None:
                y1 = torch.flip(y1, dims=[1])
            if y2 is not None:
                y2 = torch.flip(y2, dims=[1])

        if random.random() < 0.5:
            x = torch.rot90(x, k=1, dims=[1, 2])
            if y1 is not None:
                y1 = torch.rot90(y1, k=1, dims=[1, 2])
            if y2 is not None:
                y2 = torch.rot90(y2, k=1, dims=[1, 2])

        return x, y1, y2

    def __getitem__(self, idx: int):
        item = self.samples[idx]
        arr = load_input_mat(item['mat_path']).astype('float32')  # H W 3
        x = torch.from_numpy(arr).permute(2, 0, 1)               # 3 H W
        orig_h, orig_w = x.shape[1], x.shape[2]
        x = self._resize_if_needed(x)

        y_latest = None
        y_traj = None
        if 'latest_path' in item:
            y_latest = torch.from_numpy(load_mask(item['latest_path'])).unsqueeze(0)
            y_latest = self._resize_mask_if_needed(y_latest)
        if 'traj_path' in item:
            y_traj = torch.from_numpy(load_mask(item['traj_path'])).unsqueeze(0)
            y_traj = self._resize_mask_if_needed(y_traj)

        x, y_latest, y_traj = self._augment(x, y_latest, y_traj)
        cur_h, cur_w = x.shape[1], x.shape[2]

        meta = {
            'sequence': item['sequence'],
            'name': item['name'],
            'latest_idx': parse_latest_idx_from_name(item['name']),
            'orig_hw': (orig_h, orig_w),
            'input_hw': (cur_h, cur_w),
        }

        return x, y_latest, y_traj, meta


def _pad_tensor(t: torch.Tensor, out_h: int, out_w: int, value: float = 0.0) -> torch.Tensor:
    pad_h = out_h - t.shape[-2]
    pad_w = out_w - t.shape[-1]
    if pad_h < 0 or pad_w < 0:
        raise ValueError('目标 padding 尺寸小于当前张量尺寸')
    if pad_h == 0 and pad_w == 0:
        return t
    return F.pad(t, (0, pad_w, 0, pad_h), mode='constant', value=value)


def pmrk_collate_fn(batch, pad_to_multiple: int = 8):
    xs, y_latests, y_trajs, metas = zip(*batch)

    max_h = max(x.shape[-2] for x in xs)
    max_w = max(x.shape[-1] for x in xs)

    if pad_to_multiple and pad_to_multiple > 1:
        max_h = ((max_h + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple
        max_w = ((max_w + pad_to_multiple - 1) // pad_to_multiple) * pad_to_multiple

    x_batch = torch.stack([_pad_tensor(x, max_h, max_w, value=0.0) for x in xs], dim=0)

    if all(y is not None for y in y_latests):
        y_latest_batch = torch.stack([_pad_tensor(y, max_h, max_w, value=0.0) for y in y_latests], dim=0)
    else:
        y_latest_batch = None

    if all(y is not None for y in y_trajs):
        y_traj_batch = torch.stack([_pad_tensor(y, max_h, max_w, value=0.0) for y in y_trajs], dim=0)
    else:
        y_traj_batch = None

    return x_batch, y_latest_batch, y_traj_batch, list(metas)
