import os
import random
import argparse


def main():
    parser = argparse.ArgumentParser(description='扫描 Sequence* 文件夹，随机生成 train/test/val txt')
    parser.add_argument('--root_dir', type=str, required=True)
    parser.add_argument('--train_ratio', type=float, default=0.8)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--train_txt', type=str, default='train.txt')
    parser.add_argument('--test_txt', type=str, default='test.txt')
    parser.add_argument('--val_txt', type=str, default='val.txt')
    parser.add_argument('--write_val_same_as_test', action='store_true')
    args = parser.parse_args()

    seq_names = []
    for name in os.listdir(args.root_dir):
        seq_dir = os.path.join(args.root_dir, name)
        if os.path.isdir(seq_dir) and name.lower().startswith('sequence'):
            seq_names.append(name)

    seq_names = sorted(seq_names)
    if not seq_names:
        raise RuntimeError(f'在 {args.root_dir} 下没有找到 Sequence* 文件夹')

    random.seed(args.seed)
    random.shuffle(seq_names)

    n_train = max(1, int(len(seq_names) * args.train_ratio))
    train_names = sorted(seq_names[:n_train])
    test_names = sorted(seq_names[n_train:])

    if len(test_names) == 0:
        test_names = train_names[-1:]
        train_names = train_names[:-1]

    train_path = os.path.join(args.root_dir, args.train_txt)
    test_path = os.path.join(args.root_dir, args.test_txt)
    val_path = os.path.join(args.root_dir, args.val_txt)

    with open(train_path, 'w', encoding='utf-8') as f:
        for x in train_names:
            f.write(x + '\n')

    with open(test_path, 'w', encoding='utf-8') as f:
        for x in test_names:
            f.write(x + '\n')

    if args.write_val_same_as_test:
        with open(val_path, 'w', encoding='utf-8') as f:
            for x in test_names:
                f.write(x + '\n')

    print(f'train: {len(train_names)} -> {train_path}')
    print(f'test : {len(test_names)} -> {test_path}')
    if args.write_val_same_as_test:
        print(f'val  : {len(test_names)} -> {val_path}')


if __name__ == '__main__':
    main()
