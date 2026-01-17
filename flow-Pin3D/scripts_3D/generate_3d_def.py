import argparse

def parse_partition_file(partition_path):
    partition_map = {}
    with open(partition_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                partition_map[parts[0]] = int(parts[1])
    return partition_map

def modify_components(def_lines, partition_map):
    in_components = False
    new_lines = []
    for line in def_lines:
        if line.strip().startswith('COMPONENTS'):
            in_components = True
            new_lines.append(line)
            continue
        if in_components:
            if line.strip().startswith('END COMPONENTS'):
                in_components = False
                new_lines.append(line)
                continue
            if line.strip().startswith('-'):
                tokens = line.strip().split()
                if len(tokens) >= 3:
                    comp_name = tokens[1]
                    master_cell = tokens[2]
                    # Check if comp_name is in partition_map
                    part = partition_map.get(comp_name, None)
                    if part == 0:
                        master_cell += '_upper'
                    elif part == 1:
                        master_cell += '_bottom'
                    # Reconstruct the line
                    new_line = f"    - {comp_name} {master_cell} ;\n"
                    new_lines.append(new_line)
                    continue
        new_lines.append(line)
    return new_lines

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--partition', required=True)
    args = parser.parse_args()

    partition_map = parse_partition_file(args.partition)

    with open(args.input, 'r') as f:
        def_lines = f.readlines()

    new_def_lines = modify_components(def_lines, partition_map)

    with open(args.output, 'w') as f:
        f.writelines(new_def_lines)

if __name__ == '__main__':
    main()