"""
Enhanced Documentation Generator for Roblox Projects

This script generates comprehensive documentation for both Roblox games and API projects.
It supports multiple documentation types and formats, with features including:
- Full game documentation generation
- API-specific documentation
- Minimal documentation focusing on core NPC systems
- Smart file filtering using .gitignore patterns
- Tree-style directory structure visualization

Usage:
    Full documentation:
        python generate_docs.py <game_id_or_path>
    
    API documentation:
        python generate_docs.py api --api-only
    
    Minimal NPC documentation:
        python generate_docs.py <game_id> --minimal

Examples:
    python generate_docs.py sandbox-v1
    python generate_docs.py api --api-only
    python generate_docs.py sandbox-v1 --minimal
"""

import os
import json
from pathlib import Path
import argparse
import sys
from typing import Set, List, Union

def read_file_content(file_path: str) -> str:
    """
    Read and return the contents of a file with error handling.

    Args:
        file_path (str): Path to the file to read

    Returns:
        str: File contents or error message if reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def get_gitignore_patterns() -> Set[str]:
    """
    Read and parse .gitignore patterns plus default ignore patterns.

    Returns:
        Set[str]: Collection of patterns to ignore in documentation

    Note:
        Always includes certain default patterns like .git, __pycache__, etc.
        Reads additional patterns from project's .gitignore file if it exists.
    """
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
    
    project_root = Path(__file__).parent.parent
    gitignore_path = project_root / ".gitignore"
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    pattern = line.strip('/*')
                    if pattern:
                        patterns.add(pattern)
    
    return patterns

def should_skip_file(file_path: Path) -> bool:
    """
    Determine if a file should be excluded from documentation.

    Args:
        file_path (Path): Path to the file to check

    Returns:
        bool: True if file should be skipped, False otherwise

    Checks:
        - Matches against .gitignore patterns
        - Binary and image files
        - Backup files
        - Hidden files
        - Markdown files in scripts folders
    """
    skip_patterns = get_gitignore_patterns()
    path_str = str(file_path)
    
    # Skip backup files
    if '_bak' in path_str or '.bak' in path_str:
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
        return True
    
    # Skip markdown files in scripts folders
    if 'scripts' in path_str and file_path.suffix.lower() == '.md':
        return True
    
    # Check gitignore patterns
    path_parts = Path(path_str).relative_to(Path(__file__).parent.parent).parts
    return any(part in skip_patterns for part in path_parts)

def generate_tree_structure(start_path: Union[str, Path], start_with_root: bool = True) -> str:
    """
    Generate a tree-like visualization of directory structure.

    Args:
        start_path (Union[str, Path]): Root directory to start from
        start_with_root (bool): Whether to include root directory name

    Returns:
        str: Formatted string showing directory structure with proper indentation

    Example output:
        root/
        ├── folder1/
        │   ├── file1.lua
        │   └── file2.lua
        └── folder2/
            └── file3.lua
    """
    tree = []
    start_path = Path(start_path)
    
    def add_to_tree(path: Path, prefix: str = ""):
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
        for i, entry in enumerate(entries):
            if should_skip_file(Path(entry.path)):
                continue
            is_last = i == len(entries) - 1
            current_prefix = "└── " if is_last else "├── "
            display_name = Path(entry.path).relative_to(start_path).parts[-1] if not start_with_root else entry.name
            tree.append(f"{prefix}{current_prefix}{display_name}")
            if entry.is_dir():
                extension_prefix = "    " if is_last else "│   "
                add_to_tree(entry.path, prefix + extension_prefix)
    
    add_to_tree(start_path)
    return "\n".join(tree)

def get_core_npc_files() -> Set[str]:
    """
    Return set of essential NPC system files for minimal documentation.

    Returns:
        Set[str]: Set of core file names that should be included in minimal docs

    Note:
        These files represent the core NPC system functionality
        including both Lua game files and Python API files.
    """
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
    """
    Generate focused documentation for core NPC system files.

    Args:
        game_slug (str): Game identifier to generate documentation for

    Creates documentation focusing only on essential NPC system files,
    useful for understanding core functionality without peripheral code.
    """
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

def generate_documentation(path_or_id: str, api_only: bool = False):
    """
    Generate comprehensive documentation for a game or API project.

    Args:
        path_or_id (str): Game identifier or path, or 'api' for API docs
        api_only (bool): Whether to generate only API documentation

    Generates full documentation including:
    - Directory structure
    - File contents
    - Project configuration
    - API endpoints (if applicable)
    """
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

def main():
    """
    Main entry point for the documentation generator.
    
    Parses command line arguments and runs appropriate documentation generation:
    - Full game documentation
    - API-only documentation
    - Minimal NPC system documentation
    """
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