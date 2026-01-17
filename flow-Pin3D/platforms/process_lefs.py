import re

def replace_metal_numbers_in_file(file_path):

    def replacement(match):
        x = int(match.group(1))
        new_number = 21 - x
        return f'metal{new_number}'

    pattern = re.compile(r'metal(\d+)')

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        updated_content = pattern.sub(replacement, content)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        print(f"Updated content has been written back to {file_path}")
    
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except IOError as e:
        print(f"Error: Failed to read or write to the file. {e}")

import re

def extract_macros(file_path):

    pattern = re.compile(r'MACRO (\S+)')

    results = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                matches = pattern.findall(line)
                results.extend(matches)
    
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except IOError as e:
        print(f"Error: Failed to read the file. {e}")

    return results

def find_and_replace(file_path, search_text, replace_text):

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace(search_text, replace_text)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # print("File updated successfully.")
        
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except IOError:
        print("Error: Failed to read or write to the file.")

if __name__ == "__main__":

    file_path = f'nangate45_3D/lef_bottom/NangateOpenCellLibrary.macro.mod.bottom.lef'  
    macros = extract_macros(file_path)
    for macro in macros:
        find_and_replace(file_path, macro, macro+'_bottom')
    print("Extracted macros:", macros)
