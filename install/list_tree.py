import os
import fnmatch

def generate_tree(root_dir, exclude_list, max_depth):
    exclude_set = set(exclude_list.split(','))
    tree_str = []

    def tree_recursion(current_dir, prefix, current_depth):
        if current_depth > max_depth:
            return

        try:
            contents = os.listdir(current_dir)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
        
        filtered_contents = []
        for item in contents:
            if item in exclude_set:
                continue
            if any(fnmatch.fnmatch(item, pattern) for pattern in exclude_set):
                continue
            filtered_contents.append(item)
        
        pointers = ['|-- ' if i < len(filtered_contents) - 1 else '`-- ' for i in range(len(filtered_contents))]
        
        for pointer, content in zip(pointers, filtered_contents):
            path = os.path.join(current_dir, content)
            tree_str.append(f"{prefix}{pointer}{content}")
            if os.path.isdir(path):
                extension = '|   ' if pointer == '|-- ' else '    '
                tree_recursion(path, prefix + extension, current_depth + 1)

    tree_str.append(os.path.basename(root_dir))
    tree_recursion(root_dir, "", 1)
    
    return "\n".join(tree_str)

if __name__ == '__main__':
    root_directory = "./"
    absolute_root_directory = os.path.abspath(root_directory)
    
    if not os.path.exists(absolute_root_directory):
        print(f"Error: The directory '{absolute_root_directory}' does not exist.")
    else:
        exclude = "node_modules,.git,dist,.next,.gitignore,*.svg,Build,.idea,.DS_Store"
        depth = 1  # Change this to the desired depth level
        tree_output = generate_tree(absolute_root_directory, exclude, depth)
        print(tree_output)