function build_dataset_pmrk_from_root(root_dir, out_dir, win_len, current_idx, ref_idx, k_resp, smooth_sigma, bg_mode, window_mode, gamma, pts_mode, save_preview, sample_name_mode, rk_cfg, pts_cfg, pts_filter_cfg, label_cfg)

    if nargin < 3 || isempty(win_len), win_len = 33; end
    if nargin < 4 || isempty(current_idx), current_idx = 17; end
    if nargin < 5 || isempty(ref_idx), ref_idx = current_idx; end
    if nargin < 6 || isempty(k_resp), k_resp = 2.5; end
    if nargin < 7 || isempty(smooth_sigma), smooth_sigma = 1.0; end
    if nargin < 8 || isempty(bg_mode), bg_mode = 'median'; end
    if nargin < 9 || isempty(window_mode), window_mode = 'sliding'; end
    if nargin < 10 || isempty(gamma), gamma = 1.0; end
    if nargin < 11 || isempty(pts_mode), pts_mode = 'peak'; end
    if nargin < 12 || isempty(save_preview), save_preview = 1; end
    if nargin < 13 || isempty(sample_name_mode), sample_name_mode = 'start_end'; end
    if nargin < 14 || isempty(rk_cfg), rk_cfg = struct(); end
    if nargin < 15 || isempty(pts_cfg), pts_cfg = struct(); end
    if nargin < 16 || isempty(pts_filter_cfg), pts_filter_cfg = struct(); end
    if nargin < 17 || isempty(label_cfg), label_cfg = struct(); end

    if ~isfield(label_cfg, 'align_latest_mask_to_ref'), label_cfg.align_latest_mask_to_ref = 0; end
    if ~isfield(label_cfg, 'align_traj_mask_to_ref'), label_cfg.align_traj_mask_to_ref = 0; end

    if current_idx < 1 || current_idx > win_len
        error('current_idx 必须在 [1, win_len] 内');
    end
    if ref_idx < 1 || ref_idx > win_len
        error('ref_idx 必须在 [1, win_len] 内');
    end

    if ~exist(out_dir, 'dir'), mkdir(out_dir); end

    dd = dir(root_dir);
    is_valid = false(length(dd),1);
    for i = 1:length(dd)
        if dd(i).isdir
            name_i = dd(i).name;
            if ~strcmp(name_i, '.') && ~strcmp(name_i, '..')
                if length(name_i) >= 8 && strcmpi(name_i(1:8), 'Sequence')
                    is_valid(i) = true;
                end
            end
        end
    end
    seq_dirs = sort_files_by_number(dd(is_valid));
    fprintf('共找到 %d 个 Sequence 文件夹\n', length(seq_dirs));

    for s = 1:length(seq_dirs)
        seq_name = seq_dirs(s).name;
        fprintf('\n处理 %s (%d/%d)\n', seq_name, s, length(seq_dirs));

        seq_in_dir = [root_dir, '\', seq_name];
        img_dir = [seq_in_dir, '\images'];
        mask_dir = [seq_in_dir, '\masks'];

        seq_out_dir = [out_dir, '\', seq_name];
        inputs_dir = [seq_out_dir, '\inputs'];
        latest_dir = [seq_out_dir, '\mask_latest'];
        traj_dir = [seq_out_dir, '\traj_mask'];
        preview_dir = [seq_out_dir, '\previews'];

        if ~exist(seq_out_dir, 'dir'), mkdir(seq_out_dir); end
        if ~exist(inputs_dir, 'dir'), mkdir(inputs_dir); end
        if ~exist(latest_dir, 'dir'), mkdir(latest_dir); end
        if ~exist(traj_dir, 'dir'), mkdir(traj_dir); end
        if save_preview && ~exist(preview_dir, 'dir'), mkdir(preview_dir); end

        png_files = dir([img_dir, '\*.png']);
        if isempty(png_files)
            fprintf('  images下没有png，跳过\n');
            continue;
        end
        png_files = sort_files_by_number(png_files);
        num_frames = length(png_files);

        mask_exists = exist(mask_dir, 'dir') == 7;
        if mask_exists
            mask_files = sort_files_by_number(dir([mask_dir, '\*.png']));
        else
            mask_files = [];
        end

        if num_frames < win_len
            fprintf('  图像数不足 %d，跳过\n', win_len);
            continue;
        end

        switch lower(window_mode)
            case 'sliding'
                start_list = 1:(num_frames - win_len + 1);
            case 'center'
                start_mid = floor((num_frames - win_len) / 2) + 1;
                start_list = start_mid;
            otherwise
                error('window_mode 只能是 ''sliding'' 或 ''center'' ');
        end

        for w = 1:length(start_list)
            start_idx = start_list(w);
            end_idx = start_idx + win_len - 1;
            current_frame_idx = start_idx + current_idx - 1;

            switch lower(sample_name_mode)
                case 'start_end'
                    sample_name = sprintf('%03d_%03d', start_idx, end_idx);
                case 'start_current_end'
                    sample_name = sprintf('%03d_%03d_%03d', start_idx, current_frame_idx, end_idx);
                case 'current'
                    sample_name = sprintf('%03d', current_frame_idx);
                otherwise
                    error('sample_name_mode 只能是 start_end / start_current_end / current');
            end

            fprintf('  窗口 %d/%d : %s, current=%03d, ref_local=%d\n', ...
                w, length(start_list), sample_name, current_frame_idx, ref_idx);

            img_cube = read_png_cube_window(img_dir, png_files, start_idx, win_len);
            out = build_pmrk_window(img_cube, ref_idx, current_idx, k_resp, smooth_sigma, bg_mode, gamma, pts_mode, rk_cfg, pts_cfg, struct());

            input_3ch = out.input_3ch;
            P = out.P;
            P_raw = out.P_raw;
            P_filter = out.P_filter;
            H = out.H;
            M = out.M;
            Rk = out.Rk;
            Ck_raw = out.Ck_raw;
            if isfield(out, 'Ck_delta'); Ck_delta = out.Ck_delta; else; Ck_delta = []; end
            if isfield(out, 'Ck_sigma'); Ck_sigma = out.Ck_sigma; else; Ck_sigma = []; end
            max_residual = out.max_residual;
            latest_frame_idx = current_frame_idx;
            window_start_idx = start_idx;
            window_end_idx = end_idx;
            shift_xy = out.shift_xy;

            pts_filter_cfg_saved = out.pts_filter_cfg;
            save([inputs_dir, '\', sample_name, '.mat'], ...
                'input_3ch', 'P', 'P_raw', 'P_filter', 'H', 'M', 'Rk', 'Ck_raw', 'Ck_delta', 'Ck_sigma', 'max_residual', ...
                'start_idx', 'end_idx', 'window_start_idx', 'window_end_idx', ...
                'current_idx', 'current_frame_idx', 'latest_frame_idx', 'ref_idx', 'pts_mode', 'shift_xy', ...
                'rk_cfg', 'pts_cfg', 'pts_filter_cfg_saved');

            if save_preview
                save_pmrk_preview(input_3ch, [preview_dir, '\', sample_name, '.png']);
            end

            if mask_exists && length(mask_files) >= end_idx
                latest_mask = read_mask_png([mask_dir, '\', mask_files(current_frame_idx).name]);

                if label_cfg.align_latest_mask_to_ref == 1
                    dx_cur = shift_xy(current_idx, 1);
                    dy_cur = shift_xy(current_idx, 2);
                    latest_mask = shift_fill_zero(double(latest_mask), -dx_cur, -dy_cur) > 0;
                end

                imwrite(uint8(latest_mask * 255), [latest_dir, '\', sample_name, '.png']);

                traj_mask = false(size(latest_mask));
                for t = start_idx:end_idx
                    local_t = t - start_idx + 1;
                    mask_t = read_mask_png([mask_dir, '\', mask_files(t).name]);

                    if label_cfg.align_traj_mask_to_ref == 1
                        dx_t = shift_xy(local_t, 1);
                        dy_t = shift_xy(local_t, 2);
                        mask_t = shift_fill_zero(double(mask_t), -dx_t, -dy_t) > 0;
                    end

                    traj_mask = traj_mask | mask_t;
                end
                imwrite(uint8(traj_mask * 255), [traj_dir, '\', sample_name, '.png']);
            end
        end
    end

    fprintf('\n全部完成。\n');
end
