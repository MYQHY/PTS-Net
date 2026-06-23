function [P, aux] = compute_pts_independent(stab_cube, pts_cfg)

    if nargin < 2 || isempty(pts_cfg)
        pts_cfg = struct();
    end

    if ~isfield(pts_cfg, 'mode');              pts_cfg.mode = 'peak';          end
    if ~isfield(pts_cfg, 'score_mode');        pts_cfg.score_mode = 'z';       end
    if ~isfield(pts_cfg, 'z_thr');             pts_cfg.z_thr = 1.2;            end
    if ~isfield(pts_cfg, 'peak_thr');          pts_cfg.peak_thr = 0.0;         end
    if ~isfield(pts_cfg, 'gamma');             pts_cfg.gamma = 1.0;            end
    if ~isfield(pts_cfg, 'use_mad');           pts_cfg.use_mad = 1;            end
    if ~isfield(pts_cfg, 'min_score');         pts_cfg.min_score = 1e-6;       end

    if ~isfield(pts_cfg, 'pre_enhance');       pts_cfg.pre_enhance = 'dog_st'; end
    if ~isfield(pts_cfg, 'spatial_sigma');     pts_cfg.spatial_sigma = 0.8;    end
    if ~isfield(pts_cfg, 'spatial_sigma1');    pts_cfg.spatial_sigma1 = 0.8;   end
    if ~isfield(pts_cfg, 'spatial_sigma2');    pts_cfg.spatial_sigma2 = 1.8;   end
    if ~isfield(pts_cfg, 'temporal_radius');   pts_cfg.temporal_radius = 2;    end
    if ~isfield(pts_cfg, 'temporal_sigma');    pts_cfg.temporal_sigma = 1.0;   end
    if ~isfield(pts_cfg, 'pre_rectify');       pts_cfg.pre_rectify = 1;        end

    if ~isfield(pts_cfg, 'tp_radius');         pts_cfg.tp_radius = 1;          end
    if ~isfield(pts_cfg, 'tp_sigma');          pts_cfg.tp_sigma = 1.0;         end
    if ~isfield(pts_cfg, 'tp_thr');            pts_cfg.tp_thr = 0.0;           end
    if ~isfield(pts_cfg, 'tp_power');          pts_cfg.tp_power = 1.0;         end

    raw_cube = double(stab_cube);
    [H, W, T] = size(raw_cube);

    if ~isfield(pts_cfg, 'current_idx') || isempty(pts_cfg.current_idx)
        pts_cfg.current_idx = T;
    end
    current_idx = pts_cfg.current_idx;
    if current_idx < 1 || current_idx > T
        error('pts_cfg.current_idx 必须在 [1,T] 内');
    end

    [work_cube, enh_info] = pts_pre_enhance_cube(raw_cube, pts_cfg);

    temp_med = median(work_cube, 3);

    if pts_cfg.use_mad == 1
        temp_mad = median(abs(work_cube - temp_med), 3);
        temp_sigma = 1.4826 * temp_mad + 1e-6;
    else
        temp_sigma = std(work_cube, 0, 3) + 1e-6;
    end

    z_cube = zeros(H, W, T);
    peak_cube = zeros(H, W, T);

    for t = 1:T
        cur = work_cube(:, :, t);

        if t == 1
            prev = work_cube(:, :, t);
        else
            prev = work_cube(:, :, t - 1);
        end

        if t == T
            next = work_cube(:, :, t);
        else
            next = work_cube(:, :, t + 1);
        end

        z_map = (cur - temp_med) ./ temp_sigma;
        z_map = max(z_map - pts_cfg.z_thr, 0);

        peak_map = cur - 0.5 * (prev + next);
        peak_map = max(peak_map - pts_cfg.peak_thr, 0);

        z_cube(:, :, t) = z_map;
        peak_cube(:, :, t) = peak_map;
    end

    switch lower(pts_cfg.score_mode)
        case 'z'
            score_cube = z_cube;

        case 'zpeak'
            score_cube = z_cube .* (peak_cube .^ pts_cfg.gamma);

        case 'persistence'
            tp_cube = pts_temporal_smooth_cube(z_cube, pts_cfg.tp_radius, pts_cfg.tp_sigma);
            tp_cube = max(tp_cube - pts_cfg.tp_thr, 0);
            score_cube = z_cube .* (tp_cube .^ pts_cfg.tp_power);

        otherwise
            error('pts_cfg.score_mode 只能是 ''z'' / ''zpeak'' / ''persistence'' ');
    end

    switch lower(pts_cfg.mode)
        case 'peak'
            [max_score, idx] = max(score_cube, [], 3);
            P = (idx - 1) / max(T - 1, 1);
            P(max_score <= pts_cfg.min_score) = 0;

        case 'centroid'
            tt = reshape(0:T-1, 1, 1, T);
            num = sum(score_cube .* tt, 3);
            den = sum(score_cube, 3) + 1e-6;
            P = num ./ max(T - 1, 1) ./ den;
            P(den <= 1e-6) = 0;

        otherwise
            error('pts_cfg.mode 只能是 ''peak'' 或 ''centroid'' ');
    end

    P(P < 0) = 0;
    P(P > 1) = 1;

    aux = struct();
    aux.score_cube = score_cube;
    aux.current_score = score_cube(:, :, current_idx);
    aux.current_idx = current_idx;
    aux.temp_med = temp_med;
    aux.temp_sigma = temp_sigma;
    aux.z_cube = z_cube;
    aux.peak_cube = peak_cube;
    aux.enh_cube = work_cube;
    aux.raw_cube = raw_cube;
    aux.enh_info = enh_info;

    if strcmpi(pts_cfg.score_mode, 'persistence')
        aux.tp_cube = tp_cube;
    else
        aux.tp_cube = [];
    end
end

function [enh_cube, info] = pts_pre_enhance_cube(raw_cube, pts_cfg)

    [~, ~, T] = size(raw_cube);
    mode = lower(strtrim(pts_cfg.pre_enhance));

    switch mode
        case 'none'
            spatial_cube = raw_cube;

        case 'gaussian_st'
            spatial_cube = zeros(size(raw_cube));
            sigma = max(double(pts_cfg.spatial_sigma), 0);
            for t = 1:T
                spatial_cube(:, :, t) = gaussian_smooth(raw_cube(:, :, t), sigma);
            end

        case {'dog', 'dog_st'}
            spatial_cube = zeros(size(raw_cube));
            sigma1 = max(double(pts_cfg.spatial_sigma1), 0);
            sigma2 = max(double(pts_cfg.spatial_sigma2), sigma1 + 1e-6);
            for t = 1:T
                small = gaussian_smooth(raw_cube(:, :, t), sigma1);
                large = gaussian_smooth(raw_cube(:, :, t), sigma2);
                spatial_cube(:, :, t) = small - large;
            end
            if pts_cfg.pre_rectify == 1
                spatial_cube = max(spatial_cube, 0);
            end

        otherwise
            error('pts_cfg.pre_enhance 只能是 none / gaussian_st / dog / dog_st');
    end

    if strcmp(mode, 'gaussian_st') || strcmp(mode, 'dog_st')
        enh_cube = pts_temporal_smooth_cube(spatial_cube, pts_cfg.temporal_radius, pts_cfg.temporal_sigma);
    else
        enh_cube = spatial_cube;
    end

    info = struct();
    info.mode = mode;
    info.temporal_radius = pts_cfg.temporal_radius;
    info.temporal_sigma = pts_cfg.temporal_sigma;
    info.spatial_sigma = pts_cfg.spatial_sigma;
    info.spatial_sigma1 = pts_cfg.spatial_sigma1;
    info.spatial_sigma2 = pts_cfg.spatial_sigma2;
    info.pre_rectify = pts_cfg.pre_rectify;
end

function out_cube = pts_temporal_smooth_cube(in_cube, radius, sigma)

    [H, W, T] = size(in_cube);
    radius = max(0, round(radius));
    sigma = max(double(sigma), 1e-6);

    if radius <= 0
        out_cube = in_cube;
        return;
    end

    dd = -radius:radius;
    weights = exp(-(dd .^ 2) / (2 * sigma ^ 2));
    weights = weights / max(sum(weights), 1e-12);

    out_cube = zeros(H, W, T);
    for t = 1:T
        acc = zeros(H, W);
        for k = 1:numel(dd)
            tt = t + dd(k);
            if tt < 1
                tt = 1;
            elseif tt > T
                tt = T;
            end
            acc = acc + weights(k) * in_cube(:, :, tt);
        end
        out_cube(:, :, t) = acc;
    end
end
