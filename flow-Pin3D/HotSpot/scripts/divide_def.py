#!/usr/bin/env python3
import argparse
import os


def split_def_file(input_file: str, output_dir: str, base_name: str = "6_final"):
    """
    将 3D DEF 按 master 名字的后缀 (_upper / _bottom) 拆成两份：
      - <output_dir>/<base_name>_bottom.def
      - <output_dir>/<base_name>_upper.def

    除 COMPONENTS 段外的其他内容（header、PINS、NETS 等）都会完整复制到两份 DEF。
    """
    os.makedirs(output_dir, exist_ok=True)

    bottom_path = os.path.join(output_dir, f"{base_name}_bottom.def")
    upper_path  = os.path.join(output_dir, f"{base_name}_upper.def")

    with open(input_file, "r") as infile, \
         open(bottom_path, "w") as bottom_file, \
         open(upper_path, "w") as upper_file:

        inside_components = False

        for line in infile:
            stripped = line.lstrip()

            # 进入 COMPONENTS 段
            if stripped.startswith("COMPONENTS"):
                inside_components = True
                bottom_file.write(line)
                upper_file.write(line)
                continue

            # 离开 COMPONENTS 段
            if inside_components and stripped.startswith("END COMPONENTS"):
                inside_components = False
                bottom_file.write(line)
                upper_file.write(line)
                continue

            if inside_components:
                # 这里的典型行格式类似：
                #   - inst_name master_name + PLACED ( x y ) N ;
                parts = stripped.split()
                if len(parts) >= 3:
                    master = parts[2]
                    # master 形如 DFF_X1_bottom / DFF_X1_upper
                    base, _, tier = master.rpartition("_")
                    tier = tier.lower()
                    if tier == "bottom":
                        bottom_file.write(line)
                    elif tier == "upper":
                        upper_file.write(line)
                    # 其他（没有 _upper/_bottom 后缀）就不写入任何一边，
                    # 如果你希望“公共单元”同时存在于两层，可以改成：
                    # else:
                    #     bottom_file.write(line)
                    #     upper_file.write(line)
                continue

            # 不在 COMPONENTS 段：完整复制到两份 DEF
            bottom_file.write(line)
            upper_file.write(line)

    return bottom_path, upper_path


def main():
    parser = argparse.ArgumentParser(description="DEF File Splitter (upper/bottom)")
    parser.add_argument("-i", "--input", required=True, help="Input 3D DEF file path")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("--base", default="6_final", help="Base DEF name (default: 6_final)")
    args = parser.parse_args()

    bottom_path, upper_path = split_def_file(args.input, args.output, args.base)
    print(f"DEF : {bottom_path} and {upper_path}")


if __name__ == "__main__":
    main()
