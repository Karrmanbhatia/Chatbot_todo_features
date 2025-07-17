import os

def build_folder_structure(start_path, prefix='', output_lines=[]):
    items = sorted(os.listdir(start_path))
    for index, item in enumerate(items):
        path = os.path.join(start_path, item)
        connector = "├── " if index < len(items) - 1 else "└── "
        output_lines.append(prefix + connector + item)
        if os.path.isdir(path):
            extension = "│   " if index < len(items) - 1 else "    "
            build_folder_structure(path, prefix + extension, output_lines)

if __name__ == "__main__":
    root_dir = input("Enter the path to the root folder: ").strip()
    
    if os.path.isdir(root_dir):
        lines = [f"📁 Folder Structure of: {root_dir}", ""]
        build_folder_structure(root_dir, output_lines=lines)

        output_path = os.path.join(os.getcwd(), "folder_structure.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✅ Folder structure saved to: {output_path}")
    else:
        print("❌ The provided path is not a valid directory.")
