import os

# Define directories and files to exclude by name
EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', 'build', 'dist', 'objects', '.git', '.gitignore'}
EXCLUDE_FILES = {'tree.py', 'README.md'}

def generate_tree(root_dir, prefix=""):
    entries = sorted(os.listdir(root_dir))
    entries = [e for e in entries if os.path.isdir(os.path.join(root_dir, e)) or os.path.isfile(os.path.join(root_dir, e))]

    entries_to_show = [e for e in entries if e not in EXCLUDE_DIRS and e not in EXCLUDE_FILES]
    for index, entry in enumerate(entries_to_show):
        path = os.path.join(root_dir, entry)
        is_last = index == len(entries_to_show) - 1
        connector = "└─ " if is_last else "├─ "

        print(prefix + connector + entry)

        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            generate_tree(path, prefix + extension)

if __name__ == "__main__":
    root_path = os.getcwd()
    print(root_path)
    generate_tree(root_path)
