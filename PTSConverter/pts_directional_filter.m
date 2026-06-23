function out = pts_directional_filter(P, cfg)

    if nargin < 2
        cfg = struct();
    end
    if ~isfield(cfg, 'angles');        cfg.angles = 0:22.5:157.5; end
    if ~isfield(cfg, 'lengths');       cfg.lengths = [5, 7]; end
    if ~isfield(cfg, 'width');         cfg.width = 1; end
    if ~isfield(cfg, 'alpha');         cfg.alpha = 1.0; end
    if ~isfield(cfg, 'beta');          cfg.beta = 1.0; end
    if ~isfield(cfg, 'support_thr');   cfg.support_thr = 0.15; end
    if ~isfield(cfg, 'order_thr');     cfg.order_thr = 0.00; end
    if ~isfield(cfg, 'response_thr');  cfg.response_thr = 0.08; end
    if ~isfield(cfg, 'use_mask_norm'); cfg.use_mask_norm = 1; end

    P = double(P);
    P_valid = P(P > 0);
    if isempty(P_valid)
        out.R_final = zeros(size(P));
        out.keep_mask = false(size(P));
        out.best_angle_map = zeros(size(P));
        out.best_len_map = zeros(size(P));
        return;
    end

    if max(P_valid(:)) > 1.0
        pmin = min(P_valid(:));
        pmax = max(P_valid(:));
        Pn = zeros(size(P));
        if pmax > pmin
            Pn(P > 0) = (P(P > 0) - pmin) / (pmax - pmin);
        end
    else
        Pn = P;
    end

    M = double(Pn > 0);
    [H, W] = size(Pn);

    R_final = zeros(H, W);
    best_angle_map = zeros(H, W);
    best_len_map = zeros(H, W);

    for ia = 1:length(cfg.angles)
        theta = cfg.angles(ia);
        for il = 1:length(cfg.lengths)
            L = cfg.lengths(il);

            [Ksup, Kord] = make_pts_kernels(theta, L, cfg.width);

            sum_sup = sum(Ksup(:)) + 1e-6;
            Rsup_raw = conv2(M, Ksup, 'same');
            if cfg.use_mask_norm == 1
                Rsup = Rsup_raw / sum_sup;
            else
                Rsup = Rsup_raw;
            end

            Rinc = conv2(Pn, Kord, 'same');
            Rdec = conv2(Pn, -Kord, 'same');
            Rord = max(Rinc, Rdec);

            if cfg.use_mask_norm == 1
                valid_count = conv2(M, double(Ksup > 0), 'same');
                Rord = Rord ./ (valid_count + 1e-6);
            end

            Rord = max(Rord, 0);
            Rsup = max(Rsup - cfg.support_thr, 0);
            Rord = max(Rord - cfg.order_thr, 0);

            Rij = (Rsup .^ cfg.alpha) .* (Rord .^ cfg.beta);

            update_mask = Rij > R_final;
            R_final(update_mask) = Rij(update_mask);
            best_angle_map(update_mask) = theta;
            best_len_map(update_mask) = L;
        end
    end

    R_final = normalize_to_01(R_final);
    keep_mask = R_final >= cfg.response_thr;

    out.R_final = R_final;
    out.keep_mask = keep_mask;
    out.best_angle_map = best_angle_map;
    out.best_len_map = best_len_map;
end

function [Ksup, Kord] = make_pts_kernels(theta_deg, L, half_width)
    if mod(L, 2) == 0
        L = L + 1;
    end
    rad = ceil(L/2 + half_width + 2);
    [X, Y] = meshgrid(-rad:rad, -rad:rad);

    theta = theta_deg / 180 * pi;
    s =  X * cos(theta) + Y * sin(theta);
    n = -X * sin(theta) + Y * cos(theta);

    support_mask = (abs(s) <= (L-1)/2) & (abs(n) <= half_width);
    Ksup = double(support_mask);

    Kord = zeros(size(Ksup));
    if any(support_mask(:))
        vals = s(support_mask);
        if max(abs(vals)) > 0
            vals = vals / max(abs(vals));
        end
        vals = vals - mean(vals);
        Kord(support_mask) = vals;
    end
end

function x = normalize_to_01(x)
    x = double(x);
    xmax = max(x(:));
    xmin = min(x(:));
    if xmax > xmin
        x = (x - xmin) / (xmax - xmin);
    else
        x = zeros(size(x));
    end
    x(x < 0) = 0;
    x(x > 1) = 1;
end
