import math
from typing import List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

def _choose_groups(ch: int) -> int:
    for g in (8, 4, 2):
        if ch % g == 0:
            return g
    return 1

def _norm(ch: int) -> nn.GroupNorm:
    return nn.GroupNorm(_choose_groups(ch), ch)

class ResConvBlock(nn.Module):

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False)
        self.norm1 = _norm(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False)
        self.norm2 = _norm(out_ch)
        self.act = nn.ReLU(inplace=True)

        if in_ch != out_ch:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, bias=False),
                _norm(out_ch),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = self.shortcut(x)
        out = self.act(self.norm1(self.conv1(x)))
        out = self.norm2(self.conv2(out))
        out = self.act(out + identity)
        return out

class UpBlock(nn.Module):

    def __init__(self, in_ch: int, skip_ch: int, out_ch: int):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_ch, out_ch, 2, stride=2)
        self.conv = ResConvBlock(out_ch + skip_ch, out_ch)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        if x.shape[-2:] != skip.shape[-2:]:
            x = F.interpolate(x, size=skip.shape[-2:], mode='bilinear', align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)

class DilatedContextBlock(nn.Module):

    def __init__(self, ch: int, dilations: Tuple[int, ...] = (1, 2, 4)):
        super().__init__()
        branch_ch = max(ch // 2, 8)
        self.branches = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(ch, branch_ch, 3, padding=d, dilation=d, bias=False),
                _norm(branch_ch),
                nn.ReLU(inplace=True),
            )
            for d in dilations
        ])
        self.project = nn.Sequential(
            nn.Conv2d(branch_ch * len(dilations), ch, 1, bias=False),
            _norm(ch),
        )
        self.act = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = torch.cat([b(x) for b in self.branches], dim=1)
        y = self.project(y)
        return self.act(x + y)

class GatedAuxFusion(nn.Module):

    def __init__(self, ch: int, aux_scale: float = 0.5):
        super().__init__()
        self.aux_scale = float(aux_scale)
        self.gate = nn.Sequential(
            nn.Conv2d(ch * 2, ch, 3, padding=1, bias=False),
            _norm(ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(ch, ch, 1, bias=True),
            nn.Sigmoid(),
        )
        self.refine = ResConvBlock(ch, ch)

    def forward(self, pts_feat: torch.Tensor, aux_feat: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        gate = self.gate(torch.cat([pts_feat, aux_feat], dim=1))
        fused = pts_feat + self.aux_scale * gate * aux_feat
        fused = self.refine(fused)
        return fused, gate

class LearnableDirectionalPTSBank(nn.Module):

    def __init__(self, angles=(0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5),
                 lengths=(5, 7), width=1, support_thr=0.15, order_thr=0.0,
                 alpha=1.0, beta=1.0, weight_temperature=1.0):
        super().__init__()
        self.angles = tuple(float(a) for a in angles)
        self.lengths = tuple(int(l) if int(l) % 2 == 1 else int(l) + 1 for l in lengths)
        self.width = int(width)
        self.support_thr = float(support_thr)
        self.order_thr = float(order_thr)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.weight_temperature = float(weight_temperature)

        rad = max([math.ceil(L / 2 + self.width + 2) for L in self.lengths])
        yy, xx = torch.meshgrid(torch.arange(-rad, rad + 1), torch.arange(-rad, rad + 1), indexing='ij')
        xx = xx.float()
        yy = yy.float()

        support_kernels = []
        order_kernels = []
        support_sums = []
        kernel_specs: List[Tuple[float, int]] = []

        for theta_deg in self.angles:
            theta = theta_deg / 180.0 * math.pi
            s = xx * math.cos(theta) + yy * math.sin(theta)
            n = -xx * math.sin(theta) + yy * math.cos(theta)

            for L in self.lengths:
                support = ((s.abs() <= (L - 1) / 2.0) & (n.abs() <= self.width)).float()
                order = torch.zeros_like(support)
                if support.sum() > 0:
                    vals = s[support > 0]
                    max_abs = vals.abs().max().item()
                    if max_abs > 0:
                        vals = vals / max_abs
                    vals = vals - vals.mean()
                    order[support > 0] = vals
                support_kernels.append(support)
                order_kernels.append(order)
                support_sums.append(float(support.sum().item()) + 1e-6)
                kernel_specs.append((float(theta_deg), int(L)))

        self.register_buffer('support_kernels', torch.stack(support_kernels, dim=0).unsqueeze(1))
        self.register_buffer('order_kernels', torch.stack(order_kernels, dim=0).unsqueeze(1))
        self.register_buffer('support_sums', torch.tensor(support_sums, dtype=torch.float32).view(1, -1, 1, 1))
        self.padding = rad
        self.kernel_specs = kernel_specs
        self.num_kernels = len(kernel_specs)
        self.kernel_logits = nn.Parameter(torch.zeros(1, self.num_kernels, 1, 1))

    def normalized_kernel_weights(self) -> torch.Tensor:
        temperature = max(self.weight_temperature, 1e-6)
        return torch.softmax(self.kernel_logits / temperature, dim=1)

    def get_weight_table(self):
        with torch.no_grad():
            weights = self.normalized_kernel_weights().flatten().detach().cpu().tolist()
        return [
            {'angle': float(theta), 'length': int(length), 'weight': float(weight)}
            for (theta, length), weight in zip(self.kernel_specs, weights)
        ]

    def forward(self, p: torch.Tensor) -> torch.Tensor:
        m = (p > 0).float()

        rsup = F.conv2d(m, self.support_kernels, padding=self.padding)
        rsup = rsup / self.support_sums

        rinc = F.conv2d(p, self.order_kernels, padding=self.padding)
        rdec = F.conv2d(p, -self.order_kernels, padding=self.padding)
        rord = torch.maximum(rinc, rdec)

        valid_count = F.conv2d(m, (self.support_kernels > 0).float(), padding=self.padding)
        rord = rord / (valid_count + 1e-6)
        rord = F.relu(rord)

        rsup = F.relu(rsup - self.support_thr)
        rord = F.relu(rord - self.order_thr)
        r = (rsup.clamp_min(0) ** self.alpha) * (rord.clamp_min(0) ** self.beta)

        weights = self.normalized_kernel_weights()
        r = torch.sum(weights * r, dim=1, keepdim=True)

        maxv = torch.amax(r.flatten(2), dim=2, keepdim=True).unsqueeze(-1)
        minv = torch.amin(r.flatten(2), dim=2, keepdim=True).unsqueeze(-1)
        r = (r - minv) / (maxv - minv + 1e-6)
        return r.clamp(0, 1)

FixedDirectionalPTSBank = LearnableDirectionalPTSBank

class PTSMainAuxNet(nn.Module):

    def __init__(self, base_ch=32, aux_scale=0.5,
                 bank_angles=(0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5),
                 bank_lengths=(5, 7), bank_width=1):
        super().__init__()
        c1, c2, c3, c4 = base_ch, base_ch * 2, base_ch * 4, base_ch * 8
        self.aux_scale = float(aux_scale)

        self.pts_bank = LearnableDirectionalPTSBank(angles=bank_angles, lengths=bank_lengths, width=bank_width)

        self.pts_stem = ResConvBlock(2, c1)
        self.aux_stem = ResConvBlock(2, c1)
        self.fuse1 = GatedAuxFusion(c1, aux_scale=aux_scale)

        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = ResConvBlock(c1, c2)
        self.pool2 = nn.MaxPool2d(2)
        self.enc3 = ResConvBlock(c2, c3)
        self.pool3 = nn.MaxPool2d(2)

        self.bottleneck = nn.Sequential(
            ResConvBlock(c3, c4),
            DilatedContextBlock(c4, dilations=(1, 2, 4)),
        )

        self.up3 = UpBlock(c4, c3, c3)
        self.up2 = UpBlock(c3, c2, c2)
        self.up1 = UpBlock(c2, c1, c1)

        self.head_latest = nn.Conv2d(c1, 1, 1)
        self.head_traj = nn.Conv2d(c1, 1, 1)

    def forward(self, x: torch.Tensor):
        p = x[:, 0:1]
        hc = x[:, 1:3]

        p_denoise = self.pts_bank(p)
        p_feat = self.pts_stem(torch.cat([p, p_denoise], dim=1))
        a_feat = self.aux_stem(hc)

        s1, aux_gate = self.fuse1(p_feat, a_feat)
        s2 = self.enc2(self.pool1(s1))
        s3 = self.enc3(self.pool2(s2))
        b = self.bottleneck(self.pool3(s3))

        d3 = self.up3(b, s3)
        d2 = self.up2(d3, s2)
        d1 = self.up1(d2, s1)

        return {
            'latest': self.head_latest(d1),
            'traj': self.head_traj(d1),
            'pts_denoise': p_denoise,
            'aux_gate': aux_gate,
        }
