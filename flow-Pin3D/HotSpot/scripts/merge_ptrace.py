#!/usr/bin/env python3
import argparse
import sys


def load_ptrace(path: str):
    """
    读取 HotSpot .ptrace 文件，返回 (header_tokens, data_tokens)。

    当前假定文件格式为：
      <name_1> <name_2> ... <name_N>
      <p_1>    <p_2>    ... <p_N>

    如果将来你想支持多行时间步，可以在这里扩展。
    """
    with open(path, "r") as f:
        # 过滤掉空行
        lines = [ln.strip() for ln in f if ln.strip()]

    if len(lines) < 2:
        raise ValueError(f"{path} has fewer than 2 non-empty lines")

    header = lines[0].split()
    data = lines[1].split()

    if len(header) != len(data):
        raise ValueError(
            f"{path}: header length {len(header)} != data length {len(data)}"
        )

    return header, data


def coords_from(name: str):
    """
    从 grid 名字里提取坐标部分，用于上/下层对齐检查。

    兼容几种常见格式：
      - grid_0_0
      - Grid_0_0
      - upper_0_0 / bottom_0_0
    """
    parts = name.split("_")
    if len(parts) >= 3:
        # 取最后两个作为 (i, j)
        return parts[-2], parts[-1]
    elif len(parts) == 2:
        return parts[1],
    else:
        # 实在太奇怪，就原样返回
        return (name,)


def prefix_header(header, prefix: str):
    """
    给 header 里的 grid 名字加前缀，保证：
      - 如果已经是 prefix_ 开头，则保持不变；
      - 如果是 grid_0_0 / Grid_0_0 → prefix_0_0；
      - 其他名字 → prefix_<原名>。
    """
    processed = []
    for name in header:
        if name.startswith(prefix + "_"):
            processed.append(name)
            continue

        if "_" in name:
            # 如 grid_0_0 / Grid_0_0
            _, coords = name.split("_", 1)
            processed.append(f"{prefix}_{coords}")
        else:
            processed.append(f"{prefix}_{name}")
    return processed


def merge_ptrace(upper_file: str,
                 bottom_file: str,
                 output_file: str,
                 upper_prefix: str = "upper",
                 bottom_prefix: str = "bottom"):
    # 读取 upper / bottom
    try:
        u_header, u_data = load_ptrace(upper_file)
    except Exception as e:
        print(f"Error reading upper ptrace '{upper_file}': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        b_header, b_data = load_ptrace(bottom_file)
    except Exception as e:
        print(f"Error reading bottom ptrace '{bottom_file}': {e}", file=sys.stderr)
        sys.exit(1)

    if len(u_header) != len(b_header):
        print(
            f"Grid count mismatch: upper={len(u_header)}, bottom={len(b_header)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 先基于“坐标”检查上/下层 grid 是否一一对应
    for u_name, b_name in zip(u_header, b_header):
        if coords_from(u_name) != coords_from(b_name):
            print(
                f"Coordinate mismatch: {u_name} vs {b_name}",
                file=sys.stderr,
            )
            sys.exit(1)

    # 然后给 header 加上 upper_ / bottom_ 前缀
    u_header_prefixed = prefix_header(u_header, upper_prefix)
    b_header_prefixed = prefix_header(b_header, bottom_prefix)

    merged_header = u_header_prefixed + b_header_prefixed
    merged_data = u_data + b_data

    with open(output_file, "w") as f:
        f.write(" ".join(merged_header) + "\n")
        f.write(" ".join(merged_data) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Merge two ptrace files (upper + bottom)")
    parser.add_argument("-u", "--upper", required=True,
                        help="Path to the upper ptrace file")
    parser.add_argument("-b", "--bottom", required=True,
                        help="Path to the bottom ptrace file")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to the output merged ptrace file")
    parser.add_argument("--upper-prefix", default="upper",
                        help="Prefix for upper-die grids (default: upper)")
    parser.add_argument("--bottom-prefix", default="bottom",
                        help="Prefix for bottom-die grids (default: bottom)")
    args = parser.parse_args()

    merge_ptrace(
        args.upper,
        args.bottom,
        args.output,
        upper_prefix=args.upper_prefix,
        bottom_prefix=args.bottom_prefix,
    )


if __name__ == "__main__":
    main()
