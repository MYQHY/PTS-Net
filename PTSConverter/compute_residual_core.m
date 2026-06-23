function out = compute_residual_core(img_cube, ref_idx, smooth_sigma, bg_mode)

    if nargin < 2 || isempty(ref_idx)
        ref_idx = ceil(size(img_cube, 3) / 2);
    end
    if nargin < 3 || isempty(smooth_sigma)
        smooth_sigma = 1.0;
    end
    if nargin < 4 || isempty(bg_mode)
        bg_mode = 'median';
    end

    core = build_schemeB_core(img_cube, ref_idx, smooth_sigma, bg_mode);

    res_cube = core.res_cube;
    stab_cube = core.stab_cube;
    bg_img = core.bg_img;
    shift_xy = core.shift_xy;

    [~, ~, T] = size(res_cube);
    max_residual = max(res_cube, [], 3);
    last_residual = res_cube(:, :, T);
    temp_min_img = min(stab_cube, [], 3);

    out = struct();
    out.stab_cube = stab_cube;
    out.bg_img = bg_img;
    out.res_cube = res_cube;
    out.max_residual = max_residual;
    out.last_residual = last_residual;
    out.temp_min_img = temp_min_img;
    out.shift_xy = shift_xy;
end
