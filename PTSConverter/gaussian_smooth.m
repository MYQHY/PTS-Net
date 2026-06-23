function out = gaussian_smooth(img, sigma)

    if sigma <= 0
        out = img;
        return;
    end

    rad = max(1, ceil(3 * sigma));
    x = -rad:rad;
    g = exp(-(x.^2) / (2 * sigma^2));
    g = g / sum(g);

    out = conv2(conv2(double(img), g, 'same'), g', 'same');
end
