import os

def print_directory_structure(root_dir, indent=""):
    for item in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            print(f"{indent}[DIR] {item}/")
            print_directory_structure(path, indent + "    ")
        else:
            print(f"{indent}[FILE] {item}")

# To save it to a file instead of printing:
def save_directory_structure(root_dir, output_file):
    with open(output_file, 'w') as f:
        def write_structure(directory, indent=""):
            for item in sorted(os.listdir(directory)):
                path = os.path.join(directory, item)
                if os.path.isdir(path):
                    f.write(f"{indent}[DIR] {item}/\n")
                    write_structure(path, indent + "    ")
                else:
                    f.write(f"{indent}[FILE] {item}\n")
        write_structure(root_dir)

# Example usage:
# Print to console
print_directory_structure(".")

# OR save to a file
# save_directory_structure(".", "directory_structure.txt")
