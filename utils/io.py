from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from scipy.io import loadmat


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def parse_latest_idx_from_name(name: str) -> int:
    stem = Path(name).stem
    parts = stem.split('_')
    return int(parts[-1])


def load_input_mat(mat_path: str) -> np.ndarray:
    obj = loadmat(mat_path)
    if 'input_3ch' in obj:
        arr = obj['input_3ch']
    else:
        raise KeyError(f'未在 {mat_path} 中找到 input_3ch')
    return arr.astype(np.float32)


def load_mask(mask_path: str) -> np.ndarray:
    img = Image.open(mask_path).convert('L')
    # img = img.T
    arr = np.array(img, dtype=np.float32)
    # arr = arr.T
    arr = (arr > 0).astype(np.float32)
    return arr


def read_sequence_list(txt_path: Optional[str]) -> Optional[List[str]]:
    if txt_path is None:
        return None
    txt = Path(txt_path)
    if not txt.exists():
        raise FileNotFoundError(f'未找到序列列表文件: {txt_path}')
    seqs: List[str] = []
    with open(txt, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            seqs.append(Path(s).name)
    # 去重并保持顺序
    out = []
    seen = set()
    for s in seqs:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return out


def split_sequences(data_root: str, train_ratio: float = 0.8) -> Tuple[List[str], List[str]]:
    root = Path(data_root)
    seqs = sorted([p.name for p in root.iterdir() if p.is_dir() and p.name.lower().startswith('sequence')], key=lambda x: int(''.join([c for c in x if c.isdigit()]) or 0))
    n_train = max(1, int(round(len(seqs) * train_ratio)))
    n_train = min(n_train, max(len(seqs) - 1, 1)) if len(seqs) > 1 else 1
    train = seqs[:n_train]
    val = seqs[n_train:]
    if len(val) == 0:
        val = train[-1:]
        train = train[:-1] if len(train) > 1 else train
    return train, val


def collect_samples(data_root: str, sequences: Optional[List[str]], require_labels: bool = True) -> List[Dict[str, str]]:
    root = Path(data_root)
    if sequences is None:
        seq_paths = sorted([p for p in root.iterdir() if p.is_dir() and p.name.lower().startswith('sequence')], key=lambda x: int(''.join([c for c in x.name if c.isdigit()]) or 0))
    else:
        seq_paths = [root / s for s in sequences]

    samples: List[Dict[str, str]] = []
    for seq_path in seq_paths:
        if not seq_path.exists():
            continue
        inputs_dir = seq_path / 'inputs'
        latest_dir = seq_path / 'mask_latest'
        traj_dir = seq_path / 'traj_mask'
        if not inputs_dir.exists():
            continue

        for mat_path in sorted(inputs_dir.glob('*.mat')):
            name = mat_path.stem
            item: Dict[str, str] = {
                'sequence': seq_path.name,
                'name': name,
                'mat_path': str(mat_path),
            }
            latest_path = latest_dir / f'{name}.png'
            traj_path = traj_dir / f'{name}.png'

            if require_labels:
                if not latest_path.exists() or not traj_path.exists():
                    continue
                item['latest_path'] = str(latest_path)
                item['traj_path'] = str(traj_path)
            else:
                if latest_path.exists():
                    item['latest_path'] = str(latest_path)
                if traj_path.exists():
                    item['traj_path'] = str(traj_path)

            samples.append(item)
    return samples
