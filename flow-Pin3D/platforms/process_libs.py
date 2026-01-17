import re

def extract_unique_strings(file_path):

    pattern = re.compile(r'cell \((.*?)\)')
    unique_strings = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                matches = pattern.findall(line)
                unique_strings.update(matches)
                
    except FileNotFoundError:
        print("Error: The file does not exist.")
        return []
    except IOError:
        print("Error: Failed to read the file.")
        return []
    
    return list(unique_strings)

def find_and_replace(file_path, search_text, replace_text):

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace(search_text, replace_text)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("File updated successfully.")
        
    except FileNotFoundError:
        print("Error: The file does not exist.")
    except IOError:
        print("Error: Failed to read or write to the file.")

file_path = f'nangate45_3D/lib_bottom/NangateOpenCellLibrary_typical.lib' 
result = extract_unique_strings(file_path)
for string in result:
    find_and_replace(file_path, string, string+"_bottom")