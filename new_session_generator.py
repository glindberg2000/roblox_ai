import os
from pathlib import Path

# Define relevant extensions for code files
CODE_FILE_EXTENSIONS = ['.py', '.lua', '.json']
BINARY_FILE_EXTENSIONS = ['.rbxm']
DOCUMENTATION_FILES = ['README.md', 'DEV.md']
OUTPUT_FILE = 'system_prompt_source.py'
EXCLUDE_FILE_EXTENSIONS = ['.pyc', '.log', '.tmp', '.bak', '.toml']
EXCLUDE_DIRECTORIES = ['.git', '.venv', 'venv', 'env', 'roblox']
EXCLUDE_FILES = ['new_session_generator.py', 'system_prompt_source.py']
API_FILE = '../ella_www/robloxgpt.py'  # Relative path to the API file

# Function to determine if a directory is a virtual environment
def is_virtual_env(directory_name):
    common_env_patterns = ['.venv', 'venv', 'env']
    return any(directory_name.lower().startswith(pattern) for pattern in common_env_patterns) or directory_name == 'roblox'


def generate_directory_structure(base_path, ignore_patterns=None):
    """Generates a directory structure similar to the `tree` command."""
    ignore_patterns = ignore_patterns or []

    dir_structure = []

    for root, dirs, files in os.walk(base_path):
        # Ignore directories explicitly and based on ignore_patterns
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRECTORIES and not is_virtual_env(d) and not any(Path(root, d).match(pattern) for pattern in ignore_patterns)]
        # Collecting folder structure
        level = str(root).replace(str(base_path), '').count(os.sep)
        indent = ' ' * 4 * level
        dir_structure.append(f"{indent}{os.path.basename(root)}/")

        # Collecting files, excluding ignored ones
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in EXCLUDE_FILES and not any(Path(root, f).match(pattern) for pattern in ignore_patterns):
                if any(f.endswith(ext) for ext in BINARY_FILE_EXTENSIONS):
                    dir_structure.append(f"{sub_indent}{f} (binary file)")
                elif not any(f.endswith(ext) for ext in EXCLUDE_FILE_EXTENSIONS):
                    dir_structure.append(f"{sub_indent}{f}")

    return "\n".join(dir_structure)


def collect_files_content(base_path, ignore_patterns=None):
    """Collects the content of all relevant files in the directory."""
    ignore_patterns = ignore_patterns or []

    collected_content = []

    # Add documentation at the top
    for doc_file in DOCUMENTATION_FILES:
        doc_path = base_path / doc_file
        if doc_path.exists():
            with open(doc_path, 'r') as doc:
                collected_content.append(f"# {doc_file}\n")
                collected_content.append(doc.read())
                collected_content.append("\n\n")

    # Add directory structure description
    dir_structure = generate_directory_structure(base_path, ignore_patterns)
    collected_content.append("# Project Directory Structure\n")
    collected_content.append("'''\n")
    collected_content.append(dir_structure)
    collected_content.append("\n'''\n\n")

    # Traverse and add code files with directory location comments
    for root, dirs, files in os.walk(base_path):
        # Exclude unwanted directories, including virtual environments
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRECTORIES and not is_virtual_env(d) and not any(Path(root, d).match(pattern) for pattern in ignore_patterns)]

        for file in files:
            if file not in EXCLUDE_FILES and any(file.endswith(ext) for ext in CODE_FILE_EXTENSIONS):
                file_path = Path(root) / file
                if not any(file_path.match(pattern) for pattern in ignore_patterns):
                    with open(file_path, 'r') as f:
                        # Adding a comment to indicate file location
                        relative_path = os.path.relpath(file_path, base_path)
                        collected_content.append(f"# File: {relative_path}\n")
                        collected_content.append(f.read())
                        collected_content.append("\n\n")

    return "".join(collected_content)


def include_api_file(api_file_path):
    """Include the content of the API file specified by the relative path."""
    api_content = []

    api_path = Path(api_file_path)
    if api_path.exists():
        with open(api_path, 'r') as f:
            # Adding a comment to indicate file location
            relative_path = os.path.relpath(api_path, Path.cwd())
            api_content.append(f"# API File: {relative_path}\n")
            api_content.append(f.read())
            api_content.append("\n\n")

    return "".join(api_content)


def main():
    # Define base path and ignore patterns (from .gitignore or predefined)
    base_path = Path.cwd()
    ignore_patterns = []
    gitignore_path = base_path / '.gitignore'

    if gitignore_path.exists():
        with open(gitignore_path, 'r') as gitignore:
            ignore_patterns = [line.strip() for line in gitignore if line.strip() and not line.startswith('#')]

    # Collecting content to create the system prompt source file
    final_content = collect_files_content(base_path, ignore_patterns)

    # Include API endpoint content
    api_content = include_api_file(API_FILE)
    final_content += "\n# API Endpoints\n\n" + api_content

    # Writing the collected content to the output file
    with open(OUTPUT_FILE, 'w') as output_file:
        output_file.write(final_content)

    print(f"System prompt source file created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()