import os
import json
from pathlib import Path
import argparse
import sys
from typing import Set, List

def read_file_content(file_path):
    """Read and return the contents of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def get_gitignore_patterns():
    """Read patterns from .gitignore file."""
    project_root = Path(__file__).parent.parent
    gitignore_path = project_root / ".gitignore"
    patterns = {
        '.git',  # Always ignore .git directory
        '__pycache__',  # Default Python patterns
        'tests',  # Test directories
        'scripts',  # Scripts directory
        'backup',  # Backup directories
        'backups',
        '_bak',  # Backup files
        '.bak',
        'migrations',  # Database migrations
    }
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Remove leading/trailing slashes and wildcards
                    pattern = line.strip('/*')
                    if pattern:
                        patterns.add(pattern)
    
    print(f"Loaded gitignore patterns: {patterns}")  # Debug print
    return patterns

def should_skip_file(file_path):
    """Determine if a file should be skipped in documentation."""
    # Get patterns from .gitignore
    skip_patterns = get_gitignore_patterns()
    
    # Convert file_path to string for pattern matching
    path_str = str(file_path)
    
    # Skip backup files
    if '_bak' in path_str or '.bak' in path_str:
        print(f"Skipping backup file: {file_path}")
        return True
        
    # Skip binary and image files
    skip_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp',  # Images
        '.pyc', '.pyo', '.pyd',  # Python bytecode
        '.rbxm', '.rbxmx',  # Roblox models
        '.db', '.sqlite', '.sqlite3',  # Databases
        '.zip', '.tar', '.gz', '.rar',  # Archives
        '.exe', '.dll', '.so',  # Binaries
    }
    
    if file_path.suffix.lower() in skip_extensions:
        print(f"Skipping binary/image file: {file_path}")
        return True
        
    # Check if any part of the path matches skip patterns
    path_parts = Path(path_str).relative_to(Path(__file__).parent.parent).parts
    
    for part in path_parts:
        if part in skip_patterns:
            print(f"Skipping {file_path} (matched pattern: {part})")
            return True
            
    return False

def generate_tree_structure(start_path, start_with_root=True):
    """Generate a tree-like directory structure string."""
    tree = []
    start_path = Path(start_path)
    
    def add_to_tree(path, prefix=""):
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
            
            for i, entry in enumerate(entries):
                if should_skip_file(Path(entry.path)):
                    continue
                    
                is_last = i == len(entries) - 1
                current_prefix = "└── " if is_last else "├── "
                
                # Use relative path for display
                if not start_with_root:
                    display_name = Path(entry.path).relative_to(start_path).parts[-1]
                else:
                    display_name = entry.name
                    
                tree.append(f"{prefix}{current_prefix}{display_name}")
                
                if entry.is_dir():
                    extension_prefix = "    " if is_last else "│   "
                    add_to_tree(entry.path, prefix + extension_prefix)
        except Exception as e:
            tree.append(f"{prefix}Error reading directory: {str(e)}")
    
    add_to_tree(start_path)
    return "\n".join(tree)

def generate_documentation(path_or_id, api_only=False):
    project_root = Path(__file__).parent.parent
    print(f"Starting documentation generation for: {path_or_id}")
    
    # Special case for API documentation
    if path_or_id == 'api' or api_only:
        print("Generating API documentation...")
        docs_dir = project_root / "docs"
        game_name = 'api'
        game_dir = project_root / "api"
        
        # Validate API directory exists
        if not game_dir.exists():
            raise FileNotFoundError(f"API directory not found at {game_dir}")
            
        # Create docs directory if it doesn't exist
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the documentation content
        doc_content = [
            f"# API Documentation\n",
            "## Directory Structure\n",
            "```",
            "api/",
            generate_tree_structure(game_dir, start_with_root=False),
            "```\n",
            "## API Files\n"  # Section for API files
        ]
        
        # Add each file in the API directory
        files_found = False
        for file_path in game_dir.glob("**/*.*"):
            if should_skip_file(file_path):
                continue
            if file_path.name.startswith('.'):  # Skip hidden files
                continue
                
            files_found = True
            relative_path = file_path.relative_to(project_root)
            print(f"Adding file to documentation: {relative_path}")
            doc_content.extend([
                f"### {relative_path}\n",
                "```" + (file_path.suffix[1:] or 'text'),
                read_file_content(file_path),
                "```\n"
            ])
            
        if not files_found:
            print(f"No files found in {game_dir}")
            doc_content.append("*No API files found*\n")
            
        # Write the documentation to a file
        output_path = docs_dir / "DOCUMENTATION.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(doc_content))
            
        print(f"Documentation generated successfully for {game_name} at {output_path}")
        return
        
    print("WARNING: Attempting to generate game documentation - this should not happen for API docs")
    # Game documentation path (only reached if not API documentation)
    input_path = Path(os.path.expanduser(path_or_id))
    
    if input_path.is_absolute():
        game_dir = input_path
        game_name = game_dir.name
        project_root = game_dir.parent
    else:
        game_dir = project_root / "games" / str(path_or_id)
        game_name = path_or_id
        
    src_dir = game_dir / "src"
    docs_dir = project_root / "docs" / game_name
    
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found at {src_dir}")
        
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize documentation content for games
    doc_content = [
        f"# {game_name} Documentation\n",
        "## Directory Structure\n",
        "```",
        generate_tree_structure(src_dir),
        "```\n",
        "## Source Files\n"  # Added section for source files
    ]
    
    # Add Lua files content
    for file_path in src_dir.glob("**/*.lua"):
        if should_skip_file(file_path):
            continue
        if file_path.name.startswith('.'):
            continue
            
        relative_path = file_path.relative_to(src_dir)
        print(f"Adding Lua file to documentation: {relative_path}")
        doc_content.extend([
            f"### {relative_path}\n",
            "```lua",
            read_file_content(file_path),
            "```\n"
        ])
    
    # Write the documentation to a file
    output_path = docs_dir / "DOCUMENTATION.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(doc_content))
        
    print(f"Documentation generated successfully for {game_name} at {output_path}")

def get_core_npc_files() -> Set[str]:
    """Return set of core NPC system files that should be included in minimal documentation."""
    return {
        # Core NPC files
        'NPCManagerV3.lua',
        'NPCDatabaseV3.lua',
        'NPCChatHandler.lua',
        'AnimationManager.lua',
        # Core API files
        'routers_v4.py',
        'models.py',
        'conversation_managerV2.py',
        'ai_handler.py'
    }

def generate_minimal_documentation(game_slug: str):
    """Generate minimal documentation focusing on core NPC system files."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    game_dir = project_root / "games" / game_slug
    api_dir = project_root / "api"
    
    # Create docs directory
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    core_files = get_core_npc_files()
    
    # Initialize documentation content
    doc_content = [
        f"# {game_slug} NPC System Documentation (Minimal)\n",
        "## Game Directory Structure\n",
        "```",
        generate_tree_structure(game_dir / "src", start_with_root=False),
        "```\n",
        "## API Directory Structure\n",
        "```",
        generate_tree_structure(api_dir, start_with_root=False),
        "```\n",
        "## Core Game Files\n"
    ]
    
    # Add core game files
    for file_path in (game_dir / "src").rglob("*.*"):
        if file_path.name in core_files:
            relative_path = file_path.relative_to(game_dir / "src")
            print(f"Adding core game file: {relative_path}")
            doc_content.extend([
                f"### {relative_path}\n",
                "```" + (file_path.suffix[1:] or 'text'),
                read_file_content(file_path),
                "```\n"
            ])
    
    # Add API files section
    doc_content.extend([
        "## Core API Files\n"
    ])
    
    # Add core API files
    for file_path in api_dir.rglob("*.*"):
        if file_path.name in core_files:
            relative_path = file_path.relative_to(api_dir)
            print(f"Adding core API file: {relative_path}")
            doc_content.extend([
                f"### {relative_path}\n",
                "```" + (file_path.suffix[1:] or 'text'),
                read_file_content(file_path),
                "```\n"
            ])
    
    # Write minimal documentation
    output_path = docs_dir / f"{game_slug}_MINIMAL_DOCUMENTATION.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(doc_content))
        
    print(f"Minimal documentation generated successfully at {output_path}")

def main():
    """Main entry point for the documentation generator."""
    parser = argparse.ArgumentParser(description='Generate documentation for the project.')
    parser.add_argument('path_or_id', help='Path to the game directory or "api" for API documentation')
    parser.add_argument('--api-only', action='store_true', help='Generate only API documentation')
    parser.add_argument('--minimal', action='store_true', help='Generate minimal documentation focusing on core NPC system')
    
    args = parser.parse_args()
    try:
        if args.minimal:
            generate_minimal_documentation(args.path_or_id)
        else:
            generate_documentation(args.path_or_id, args.api_only)
    except Exception as e:
        print(f"Error generating documentation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 