function img_cube = read_png_cube_window(img_dir, png_files, start_idx, win_len)

    end_idx = start_idx + win_len - 1;
    if end_idx > length(png_files)
        error('读取窗口越界');
    end

    img0 = imread([img_dir, '\', png_files(start_idx).name]);
    if ndims(img0) == 3
        img0 = rgb2gray(img0);
    end
    img0 = double(img0);

    [H, W] = size(img0);
    img_cube = zeros(H, W, win_len);
    img_cube(:, :, 1) = img0;

    for k = 2:win_len
        img = imread([img_dir, '\', png_files(start_idx + k - 1).name]);
        if ndims(img) == 3
            img = rgb2gray(img);
        end
        img_cube(:, :, k) = double(img);
    end
end
