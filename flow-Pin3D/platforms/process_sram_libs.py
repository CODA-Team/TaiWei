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

if __name__ == "__main__":
    ids = ["32x32", "32x64", "64x7", "64x15", "64x21", "64x32", "64x62", "64x64", "64x96", "64x124", "128x32", "128x116", "128x256", "256x16", "256x32", "256x34", "256x48", "256x95", "256x96", "512x64", "1024x32", "2048x39"]
    for fakeram_id in ids:
        filename = f'nangate45_3D/lib_upper/fakeram45_{fakeram_id}.lib'
        find_and_replace(filename, f"fakeram45_{fakeram_id}", f"fakeram45_{fakeram_id}_upper")