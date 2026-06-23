%% Copyright © 2026 PTS-Net Authors. All rights reserved.
% date:06/23/2026
% description: make pts,hotspot,evidence


%% change your dir
clc;
clear;
close all;

proj_dir = fileparts(mfilename('fullpath'));
cd(proj_dir);
addpath(genpath(proj_dir));

root_dir = 'F:\dataset';  % example: xxxx/EWIRSTD
out_dir = 'F:\PTSoutput';   % example: xxxx/EWIRSTD_PTS



%% 
win_len = 33;
current_idx = 17;
ref_idx = 17;
k_resp = 2.5;
smooth_sigma = 1.0;
bg_mode = 'median';
window_mode = 'sliding';
gamma = 1.0;
pts_mode = 'peak';
save_preview = 1;
sample_name_mode = 'start_end';

pts_cfg = struct();
pts_cfg.mode = 'peak';
pts_cfg.score_mode = 'z';
pts_cfg.z_thr = 1.2;
pts_cfg.peak_thr = 0.0;
pts_cfg.gamma = 1.0;
pts_cfg.use_mad = 1;
pts_cfg.min_score = 1e-7;
pts_cfg.current_idx = current_idx;
pts_cfg.pre_enhance = 'dog_st';
pts_cfg.spatial_sigma = 0.8;
pts_cfg.spatial_sigma1 = 0.8;
pts_cfg.spatial_sigma2 = 1.8;
pts_cfg.temporal_radius = 2;
pts_cfg.temporal_sigma = 1.0;
pts_cfg.pre_rectify = 1;
pts_cfg.tp_radius = 1;
pts_cfg.tp_sigma = 1.0;
pts_cfg.tp_thr = 0.0;
pts_cfg.tp_power = 1.0;

rk_cfg = struct();
rk_cfg.hot_source = 'enhanced';
rk_cfg.hot_mode = 'percentile';
rk_cfg.hot_percentile = 95;
rk_cfg.hot_norm_p1 = 5;
rk_cfg.hot_norm_p99 = 98;
rk_cfg.hot_gamma = 1.5;
rk_cfg.ck_source = 'enhanced';
rk_cfg.ck_norm_p1 = 1;
rk_cfg.ck_norm_p99 = 99;
rk_cfg.ck_gamma = 0.7;
rk_cfg.ck_thr = 0.0;
rk_cfg.ck_sigma_scale = 0.5;

pts_filter_cfg = struct();
pts_filter_cfg.enable = 0;

label_cfg = struct();
label_cfg.align_latest_mask_to_ref = 0;
label_cfg.align_traj_mask_to_ref = 0;

build_dataset_pmrk_from_root(root_dir, out_dir, win_len, current_idx, ref_idx, k_resp, smooth_sigma, bg_mode, window_mode, gamma, pts_mode, save_preview, sample_name_mode, rk_cfg, pts_cfg, pts_filter_cfg, label_cfg);
