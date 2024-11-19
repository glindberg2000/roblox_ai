import os
import json
from pathlib import Path
import argparse

def read_file_content(file_path):
    """Read and return the contents of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def generate_tree_structure(start_path):
    """Generate a tree-like directory structure string."""
    tree = []
    start_path = Path(start_path)
    
    def add_to_tree(path, prefix=""):
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
            
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                current_prefix = "└── " if is_last else "├── "
                
                tree.append(f"{prefix}{current_prefix}{entry.name}")
                
                if entry.is_dir():
                    extension_prefix = "    " if is_last else "│   "
                    add_to_tree(entry.path, prefix + extension_prefix)
        except Exception as e:
            tree.append(f"{prefix}Error reading directory: {str(e)}")
    
    add_to_tree(start_path)
    return "\n".join(tree)

def generate_documentation(path_or_id):
    # Determine if input is a full path or game ID
    input_path = Path(os.path.expanduser(path_or_id))
    
    if input_path.is_absolute():
        # Using full path
        game_dir = input_path
        game_name = game_dir.name
        project_root = game_dir.parent
    else:
        # Using game ID
        project_root = Path(__file__).parent.parent
        game_dir = project_root / "games" / str(path_or_id)
        game_name = path_or_id
    
    src_dir = game_dir / "src"
    docs_dir = project_root / "docs" / game_name
    
    # Validate source directory exists
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found at {src_dir}")
    
    # Create docs directory if it doesn't exist
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the documentation content
    doc_content = [
        f"# {game_name} Documentation\n",
        "## Directory Structure\n",
        "```",
        f"{game_dir}/",
        generate_tree_structure(game_dir),
        "```\n",
        "## Project Configuration\n"
    ]
    
    # Add project configuration if it exists
    project_config = game_dir / "default.project.json"
    if project_config.exists():
        doc_content.extend([
            "```json",
            read_file_content(project_config),
            "```\n"
        ])
    else:
        doc_content.append("*No default.project.json found*\n")
    
    doc_content.append("## Source Files\n")
    
    # Categories for organizing files
    categories = {
        "client": "### Client Scripts",
        "server": "### Server Scripts",
        "shared": "### Shared Scripts",
        "data": "### Data Scripts",
        "services": "### Services",
        "config": "### Configuration",
        "debug": "### Debug Scripts"
    }
    
    # Add files by category
    for category, header in categories.items():
        category_path = src_dir / category
        if category_path.exists():
            doc_content.extend([
                f"{header}\n"
            ])
            
            # Add each Lua file in the category
            for file_path in category_path.glob("**/*.lua"):
                relative_path = file_path.relative_to(game_dir)
                doc_content.extend([
                    f"#### {relative_path}\n",
                    "```lua",
                    read_file_content(file_path),
                    "```\n"
                ])
    
    # Write the documentation to a file
    output_path = docs_dir / "DOCUMENTATION.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(doc_content))
    
    print(f"Documentation generated successfully for {game_name} at {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate documentation for a Roblox game.')
    parser.add_argument('path_or_id', 
                       help='Either a game ID (e.g., 666) or a full path (e.g., ~/dev/roblox/game_template)')
    
    args = parser.parse_args()
    try:
        generate_documentation(args.path_or_id)
    except Exception as e:
        print(f"Error generating documentation: {str(e)}") 