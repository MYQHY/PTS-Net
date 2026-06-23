function [dx, dy] = estimate_shift_phasecorr(img1, img2)

    img1 = double(img1);
    img2 = double(img2);

    img1 = img1 - mean(img1(:));
    img2 = img2 - mean(img2(:));

    F1 = fft2(img1);
    F2 = fft2(img2);

    R = F1 .* conj(F2);
    R = R ./ (abs(R) + 1e-12);

    corr = real(ifft2(R));

    [H, W] = size(corr);
    [~, idx] = max(corr(:));
    [r, c] = ind2sub([H, W], idx);

    dx = r - 1;
    dy = c - 1;

    if dx > H / 2
        dx = dx - H;
    end
    if dy > W / 2
        dy = dy - W;
    end

    dx = round(dx);
    dy = round(dy);
end
