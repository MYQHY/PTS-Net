function save_pmrk_preview(input_3ch, save_path)

    rgb = zeros(size(input_3ch));
    rgb(:, :, 1) = input_3ch(:, :, 1);
    rgb(:, :, 2) = input_3ch(:, :, 2);
    rgb(:, :, 3) = input_3ch(:, :, 3);

    rgb(rgb < 0) = 0;
    rgb(rgb > 1) = 1;

    imwrite(rgb, save_path);
end
