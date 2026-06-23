function out = build_pmrk_window(img_cube, ref_idx, current_idx, k_resp, smooth_sigma, bg_mode, gamma, pts_mode, rk_cfg, pts_cfg, pts_filter_cfg)

    if nargin < 2 || isempty(ref_idx), ref_idx = ceil(size(img_cube, 3) / 2); end
    if nargin < 3 || isempty(current_idx), current_idx = ref_idx; end
    if nargin < 5 || isempty(smooth_sigma), smooth_sigma = 1.0; end
    if nargin < 6 || isempty(bg_mode), bg_mode = 'median'; end
    if nargin < 7 || isempty(gamma), gamma = 1.0; end
    if nargin < 8 || isempty(pts_mode), pts_mode = 'peak'; end
    if nargin < 9 || isempty(rk_cfg), rk_cfg = struct(); end
    if nargin < 10 || isempty(pts_cfg), pts_cfg = struct(); end
    if nargin < 11 || isempty(pts_filter_cfg), pts_filter_cfg = struct(); end

    [~, ~, T] = size(img_cube);
    if ref_idx < 1 || ref_idx > T
        error('ref_idx 必须在 [1,T] 内');
    end
    if current_idx < 1 || current_idx > T
        error('current_idx 必须在 [1,T] 内');
    end

    if ~isfield(pts_cfg, 'mode') || isempty(pts_cfg.mode), pts_cfg.mode = pts_mode; end
    if ~isfield(pts_cfg, 'score_mode') || isempty(pts_cfg.score_mode), pts_cfg.score_mode = 'z'; end
    if ~isfield(pts_cfg, 'z_thr') || isempty(pts_cfg.z_thr), pts_cfg.z_thr = 1.2; end
    if ~isfield(pts_cfg, 'peak_thr') || isempty(pts_cfg.peak_thr), pts_cfg.peak_thr = 0.0; end
    if ~isfield(pts_cfg, 'gamma') || isempty(pts_cfg.gamma), pts_cfg.gamma = 1.0; end
    if ~isfield(pts_cfg, 'use_mad') || isempty(pts_cfg.use_mad), pts_cfg.use_mad = 1; end
    if ~isfield(pts_cfg, 'min_score') || isempty(pts_cfg.min_score), pts_cfg.min_score = 1e-6; end
    if ~isfield(pts_cfg, 'pre_enhance') || isempty(pts_cfg.pre_enhance), pts_cfg.pre_enhance = 'dog_st'; end
    if ~isfield(pts_cfg, 'spatial_sigma') || isempty(pts_cfg.spatial_sigma), pts_cfg.spatial_sigma = 0.8; end
    if ~isfield(pts_cfg, 'spatial_sigma1') || isempty(pts_cfg.spatial_sigma1), pts_cfg.spatial_sigma1 = 0.8; end
    if ~isfield(pts_cfg, 'spatial_sigma2') || isempty(pts_cfg.spatial_sigma2), pts_cfg.spatial_sigma2 = 1.8; end
    if ~isfield(pts_cfg, 'temporal_radius') || isempty(pts_cfg.temporal_radius), pts_cfg.temporal_radius = 2; end
    if ~isfield(pts_cfg, 'temporal_sigma') || isempty(pts_cfg.temporal_sigma), pts_cfg.temporal_sigma = 1.0; end
    if ~isfield(pts_cfg, 'pre_rectify') || isempty(pts_cfg.pre_rectify), pts_cfg.pre_rectify = 1; end
    if ~isfield(pts_cfg, 'tp_radius') || isempty(pts_cfg.tp_radius), pts_cfg.tp_radius = 1; end
    if ~isfield(pts_cfg, 'tp_sigma') || isempty(pts_cfg.tp_sigma), pts_cfg.tp_sigma = 1.0; end
    if ~isfield(pts_cfg, 'tp_thr') || isempty(pts_cfg.tp_thr), pts_cfg.tp_thr = 0.0; end
    if ~isfield(pts_cfg, 'tp_power') || isempty(pts_cfg.tp_power), pts_cfg.tp_power = 1.0; end
    pts_cfg.current_idx = current_idx;

    if ~isfield(rk_cfg, 'hot_source') || isempty(rk_cfg.hot_source), rk_cfg.hot_source = 'enhanced'; end
    if ~isfield(rk_cfg, 'hot_mode') || isempty(rk_cfg.hot_mode), rk_cfg.hot_mode = 'percentile'; end
    if ~isfield(rk_cfg, 'hot_percentile') || isempty(rk_cfg.hot_percentile), rk_cfg.hot_percentile = 95; end
    if ~isfield(rk_cfg, 'hot_norm_p1') || isempty(rk_cfg.hot_norm_p1), rk_cfg.hot_norm_p1 = 5; end
    if ~isfield(rk_cfg, 'hot_norm_p99') || isempty(rk_cfg.hot_norm_p99), rk_cfg.hot_norm_p99 = 98; end
    if ~isfield(rk_cfg, 'hot_gamma') || isempty(rk_cfg.hot_gamma), rk_cfg.hot_gamma = 1.5; end

    if ~isfield(rk_cfg, 'ck_source') || isempty(rk_cfg.ck_source), rk_cfg.ck_source = 'enhanced'; end
    if ~isfield(rk_cfg, 'ck_norm_p1') || isempty(rk_cfg.ck_norm_p1), rk_cfg.ck_norm_p1 = 1; end
    if ~isfield(rk_cfg, 'ck_norm_p99') || isempty(rk_cfg.ck_norm_p99), rk_cfg.ck_norm_p99 = 99; end
    if ~isfield(rk_cfg, 'ck_gamma') || isempty(rk_cfg.ck_gamma), rk_cfg.ck_gamma = 0.7; end
    if ~isfield(rk_cfg, 'ck_thr') || isempty(rk_cfg.ck_thr)
        if isfield(rk_cfg, 'ck_min') && ~isempty(rk_cfg.ck_min)
            rk_cfg.ck_thr = rk_cfg.ck_min;
        else
            rk_cfg.ck_thr = 0.0;
        end
    end
    if ~isfield(rk_cfg, 'ck_sigma_scale') || isempty(rk_cfg.ck_sigma_scale), rk_cfg.ck_sigma_scale = 0.5; end

    core = compute_residual_core(img_cube, ref_idx, smooth_sigma, bg_mode);
    stab_cube = core.stab_cube;
    res_cube = core.res_cube;
    max_residual = core.max_residual;
    temp_min_img = core.temp_min_img;
    bg_img = core.bg_img;
    shift_xy = core.shift_xy;

    [P, pts_aux] = compute_pts_independent(stab_cube, pts_cfg);
    P_raw = P;
    P_filter = zeros(size(P));
    enh_cube = pts_aux.enh_cube;

    switch lower(rk_cfg.hot_source)
        case 'enhanced'
            enh_bg = median(enh_cube, 3);
            hot_cube = max(enh_cube - enh_bg, 0);
        case 'residual'
            hot_cube = res_cube;
        otherwise
            error('rk_cfg.hot_source 只能是 ''enhanced'' 或 ''residual'' ');
    end

    switch lower(rk_cfg.hot_mode)
        case 'max'
            Hraw = max(hot_cube, [], 3);
        case 'percentile'
            Hraw = prctile(hot_cube, rk_cfg.hot_percentile, 3);
        otherwise
            error('rk_cfg.hot_mode 只能是 ''max'' 或 ''percentile'' ');
    end
    H = robust_normalize_custom(Hraw, rk_cfg.hot_norm_p1, rk_cfg.hot_norm_p99);
    if abs(rk_cfg.hot_gamma - 1.0) > 1e-8
        H = H .^ rk_cfg.hot_gamma;
    end
    H(H < 0) = 0;
    H(H > 1) = 1;
    M = H;

    switch lower(rk_cfg.ck_source)
        case 'enhanced'
            ck_cube = enh_cube;
        case 'stable'
            ck_cube = stab_cube;
        otherwise
            error('rk_cfg.ck_source 只能是 ''enhanced'' 或 ''stable'' ');
    end

    ck_min_img = min(ck_cube, [], 3);
    ck_med_img = median(ck_cube, 3);
    ck_mad_img = median(abs(ck_cube - ck_med_img), 3);
    ck_sigma_img = 1.4826 * ck_mad_img + 1e-6;

    Ik = double(ck_cube(:, :, current_idx));
    Ck_delta = max(Ik - ck_min_img, 0);
    Ck_raw = max(Ck_delta - rk_cfg.ck_thr - rk_cfg.ck_sigma_scale * ck_sigma_img, 0);
    Rk = robust_normalize_custom(Ck_raw, rk_cfg.ck_norm_p1, rk_cfg.ck_norm_p99);
    if abs(rk_cfg.ck_gamma - 1.0) > 1e-8
        Rk = Rk .^ rk_cfg.ck_gamma;
    end
    Rk(Rk < 0) = 0;
    Rk(Rk > 1) = 1;

    input_3ch = cat(3, P, H, Rk);

    out = struct();
    out.input_3ch = input_3ch;
    out.P_raw = P_raw;
    out.P_filter = P_filter;
    out.P = P;
    out.H = H;
    out.M = M;
    out.Rk = Rk;
    out.Ck_raw = Ck_raw;
    out.Ck_delta = Ck_delta;
    out.Ck_sigma = ck_sigma_img;
    out.max_residual = max_residual;
    out.shift_xy = shift_xy;
    out.res_cube = res_cube;
    out.stab_cube = stab_cube;
    out.enh_cube = enh_cube;
    out.bg_img = bg_img;
    out.temp_min_img = temp_min_img;
    out.rk_cfg = rk_cfg;
    out.pts_cfg = pts_cfg;
    out.ref_idx = ref_idx;
    out.current_idx = current_idx;
    out.pts_filter_cfg = struct('enable', 0, 'note', 'MATLAB side disabled');
    out.pts_score_cube = pts_aux.score_cube;
    out.pts_aux = pts_aux;
end
