function files_sorted = sort_files_by_number(files_in)

    n = length(files_in);
    nums = zeros(n,1);

    for i = 1:n
        name_i = files_in(i).name;
        token = regexp(name_i, '\d+', 'match');
        if isempty(token)
            nums(i) = inf;
        else
            nums(i) = str2double(token{1});
        end
    end

    [~, idx] = sort(nums);
    files_sorted = files_in(idx);
end
