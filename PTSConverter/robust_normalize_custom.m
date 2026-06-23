function out = robust_normalize_custom(img, p1v, p99v)

    if nargin < 2 || isempty(p1v)
        p1v = 1;
    end
    if nargin < 3 || isempty(p99v)
        p99v = 99;
    end

    img = double(img);

    lo = prctile(img(:), p1v);
    hi = prctile(img(:), p99v);

    if hi <= lo
        lo = min(img(:));
        hi = max(img(:));
    end

    if hi > lo
        out = (img - lo) / (hi - lo);
    else
        out = zeros(size(img));
    end

    out(out < 0) = 0;
    out(out > 1) = 1;
end
