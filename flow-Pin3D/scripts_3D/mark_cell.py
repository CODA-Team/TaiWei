import argparse

def modify_components(def_lines, backfix, status, exclude_list):
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
                    if master_cell.endswith(backfix) and comp_name not in exclude_list:
                        parts = line.split('+')
                        if len(parts) == 2:
                            left = parts[0]
                            right = parts[1]
                            right_tokens = right.strip().split()
                            if right_tokens:
                                right_tokens[0] = status
                                new_line = left + '+ ' + ' '.join(right_tokens) + '\n'
                                new_lines.append(new_line)
                                continue
        new_lines.append(line)
    return new_lines

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--backfix', required=True)
    parser.add_argument('--status', required=True, help='Status to assign (e.g., FIXED)')
    parser.add_argument('--exclude', nargs='*', default=[], help='List of component names to exclude')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        def_lines = f.readlines()

    new_def_lines = modify_components(def_lines, args.backfix, args.status, args.exclude)

    with open(args.output, 'w') as f:
        f.writelines(new_def_lines)

if __name__ == '__main__':
    main()