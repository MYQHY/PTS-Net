function out = shift_fill_zero(img, dx, dy)

    [H, W] = size(img);
    out = zeros(H, W);

    src_r1 = max(1, 1 - dx);
    src_r2 = min(H, H - dx);
    dst_r1 = max(1, 1 + dx);
    dst_r2 = min(H, H + dx);

    src_c1 = max(1, 1 - dy);
    src_c2 = min(W, W - dy);
    dst_c1 = max(1, 1 + dy);
    dst_c2 = min(W, W + dy);

    if src_r1 <= src_r2 && src_c1 <= src_c2 && dst_r1 <= dst_r2 && dst_c1 <= dst_c2
        out(dst_r1:dst_r2, dst_c1:dst_c2) = img(src_r1:src_r2, src_c1:src_c2);
    end
end
