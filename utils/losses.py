import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):
    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        prob = torch.sigmoid(logits)
        prob = prob.contiguous().view(prob.size(0), -1)
        target = target.contiguous().view(target.size(0), -1)
        inter = (prob * target).sum(dim=1)
        denom = prob.sum(dim=1) + target.sum(dim=1)
        dice = (2 * inter + self.smooth) / (denom + self.smooth)
        return 1 - dice.mean()


class BinaryFocalLoss(nn.Module):
    def __init__(self, alpha: float = 0.9, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, target, reduction='none')
        prob = torch.sigmoid(logits)
        pt = torch.where(target > 0.5, prob, 1 - prob)
        alpha_t = torch.where(target > 0.5, torch.full_like(target, self.alpha), torch.full_like(target, 1 - self.alpha))
        loss = alpha_t * ((1 - pt) ** self.gamma) * bce
        return loss.mean()


class DualHeadLoss(nn.Module):
    """
    相比旧版，增加 traj 头权重，避免网络只学热点/当前帧捷径。
    """
    def __init__(self, lambda_latest: float = 1.0, lambda_traj: float = 0.6):
        super().__init__()
        self.lambda_latest = lambda_latest
        self.lambda_traj = lambda_traj
        self.latest_focal = BinaryFocalLoss(alpha=0.9, gamma=2.0)
        self.latest_dice = DiceLoss()
        self.traj_focal = BinaryFocalLoss(alpha=0.85, gamma=2.0)
        self.traj_dice = DiceLoss()

    def forward(self, logits_latest: torch.Tensor, target_latest: torch.Tensor,
                logits_traj: torch.Tensor, target_traj: torch.Tensor) -> torch.Tensor:
        loss_latest = self.latest_focal(logits_latest, target_latest) + 0.3 * self.latest_dice(logits_latest, target_latest)
        loss_traj = self.traj_focal(logits_traj, target_traj) + 0.5 * self.traj_dice(logits_traj, target_traj)
        return self.lambda_latest * loss_latest + self.lambda_traj * loss_traj
