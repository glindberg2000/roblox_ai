import os
import json

def check_project_structure(root_dir):
    print("Checking project structure...")
    
    # Check if default.project.json exists
    if not os.path.exists(os.path.join(root_dir, "default.project.json")):
        print("Error: default.project.json not found in the root directory.")
        return

    # Load and parse default.project.json
    with open(os.path.join(root_dir, "default.project.json"), "r") as f:
        try:
            project_json = json.load(f)
        except json.JSONDecodeError:
            print("Error: default.project.json is not a valid JSON file.")
            return

    # Function to recursively check paths in the JSON
    def check_paths(node, current_path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$path":
                    full_path = os.path.join(root_dir, value)
                    if not os.path.exists(full_path):
                        print(f"Error: Path not found: {full_path}")
                    else:
                        print(f"Found: {full_path}")
                else:
                    check_paths(value, os.path.join(current_path, key))
        elif isinstance(node, list):
            for item in node:
                check_paths(item, current_path)

    # Start checking paths
    check_paths(project_json, "")

    # Check for src directory and its subdirectories
    src_dir = os.path.join(root_dir, "src")
    if not os.path.exists(src_dir):
        print("Error: src directory not found.")
    else:
        print("Found src directory.")
        for subdir in ["shared", "server", "client", "data", "assets"]:
            subdir_path = os.path.join(src_dir, subdir)
            if os.path.exists(subdir_path):
                print(f"Found: {subdir_path}")
            else:
                print(f"Warning: {subdir_path} not found.")

    print("Project structure check completed.")

if __name__ == "__main__":
    root_directory = os.path.dirname(os.path.abspath(__file__))
    check_project_structure(root_directory)