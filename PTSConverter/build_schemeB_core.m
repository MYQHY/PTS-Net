function out = build_schemeB_core(img_cube, ref_idx, smooth_sigma, bg_mode)

    [H, W, T] = size(img_cube);
    img_cube = double(img_cube);

    ref_img = img_cube(:, :, ref_idx);
    if smooth_sigma > 0
        ref_img_use = gaussian_smooth(ref_img, smooth_sigma);
    else
        ref_img_use = ref_img;
    end

    stab_cube = zeros(H, W, T);
    shift_xy = zeros(T, 2);

    for t = 1:T
        cur_img = img_cube(:, :, t);
        if smooth_sigma > 0
            cur_img_use = gaussian_smooth(cur_img, smooth_sigma);
        else
            cur_img_use = cur_img;
        end

        [dx, dy] = estimate_shift_phasecorr(cur_img_use, ref_img_use);
        stab_cube(:, :, t) = shift_fill_zero(cur_img, -dx, -dy);
        shift_xy(t, :) = [dx, dy];
    end

    switch lower(bg_mode)
        case 'median'
            bg_img = median(stab_cube, 3);
        case 'mean'
            bg_img = mean(stab_cube, 3);
        otherwise
            error('bg_mode 只能是 ''median'' 或 ''mean'' ');
    end

    res_cube = zeros(H, W, T);
    for t = 1:T
        tmp = stab_cube(:, :, t) - bg_img;
        tmp(tmp < 0) = 0;
        res_cube(:, :, t) = tmp;
    end

    out = struct();
    out.stab_cube = stab_cube;
    out.bg_img = bg_img;
    out.res_cube = res_cube;
    out.shift_xy = shift_xy;
end
