function mask = read_mask_png(mask_path)

    img = imread(mask_path);
    if ndims(img) == 3
        img = rgb2gray(img);
    end
    mask = img > 0;
end
