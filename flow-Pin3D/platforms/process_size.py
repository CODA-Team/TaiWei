import os
import re

def modify_file_content(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    pattern = re.compile(r'^\s*SIZE\s+(\d+\.\d+)\s+BY\s+(\d+\.\d+)\s*;\s*$')

    new_lines = []
    for line in lines:

        match = pattern.match(line)
        if match:

            new_line = "  SIZE 0.19 BY 1.4 ;\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

def process_directory(directory):

    for root, dirs, files in os.walk(directory):
        for file in files:

            if file.endswith('.lef'):
                file_path = os.path.join(root, file)

                modify_file_content(file_path)
                print(f"Modified {file_path}")

directory_path = 'nangate45_3D/lef/'
process_directory(directory_path)