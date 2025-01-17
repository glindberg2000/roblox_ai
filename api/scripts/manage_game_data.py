import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from api.app.config import BASE_DIR, get_game_paths
from api.app.utils import get_database_paths, save_lua_database
from api.app.database import get_db, generate_lua_from_db, import_json_to_db
from typing import Optional

USAGE_EXAMPLES = """
Game Data Management Tool
------------------------

This tool manages game data files including backups, initialization, and Lua generation.

Examples:
    # Initialize game1 from backup data
    python -m api.scripts.manage_game_data game1 --action init --source-dir ~/dev/roblox/backups/data
    
    # Create a backup of current game1 data
    python -m api.scripts.manage_game_data game1 --action backup
    
    # Restore game1 from latest backup
    python -m api.scripts.manage_game_data game1 --action restore
    
    # Generate only Lua files for game1
    python -m api.scripts.manage_game_data game1 --action lua
    
    # List available backups for game1
    python -m api.scripts.manage_game_data game1 --action list-backups

Directory Structure:
    backups/                     # Source backups
    └── data/
        ├── AssetDatabase.json   # Source asset data
        └── NPCDatabase.json     # Source NPC data
    
    games/                       # Game directories
    └── game1/
        ├── backups/            # Game-specific backups
        │   └── YYYY-MM-DD_HH-MM-SS/
        │       ├── AssetDatabase.json
        │       └── NPCDatabase.json
        └── src/
            └── data/
                ├── AssetDatabase.json
                ├── AssetDatabase.lua
                ├── NPCDatabase.json
                └── NPCDatabase.lua
"""

def get_backup_dir(game_slug: str, create_new: bool = False) -> Path:
    """Get the backup directory for a game"""
    game_paths = get_game_paths(game_slug)
    backup_base = game_paths['root'] / "backups"
    
    if create_new:
        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = backup_base / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    # For restore, get latest backup
    if backup_base.exists():
        backups = sorted(backup_base.iterdir(), reverse=True)
        if backups:
            return backups[0]
    
    return backup_base

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file safely"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def save_json_file(file_path: Path, data: dict) -> None:
    """Save data to a JSON file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def restore_from_backup(game_slug: str) -> None:
    """Restore game data from latest backup"""
    print(f"\nRestoring {game_slug} from backup...")
    
    backup_dir = get_backup_dir(game_slug)
    if not backup_dir.exists():
        print(f"No backups found for {game_slug}")
        return
    
    print(f"Using backup from: {backup_dir}")
    db_paths = get_database_paths(game_slug)
    
    # Copy JSON files from backup
    for db_type in ['asset', 'npc']:
        backup_file = backup_dir / f"{db_type.capitalize()}Database.json"
        if backup_file.exists():
            print(f"Restoring {db_type} data from {backup_file}")
            shutil.copy2(backup_file, db_paths[db_type]['json'])
            
            # Generate Lua file from restored JSON
            data = load_json_file(db_paths[db_type]['json'])
            save_lua_database(db_paths[db_type]['lua'], data)
            print(f"Generated Lua file at {db_paths[db_type]['lua']}")

def list_backups(game_slug: str) -> None:
    """List available backups for a game"""
    game_paths = get_game_paths(game_slug)
    backup_base = game_paths['root'] / "backups"
    
    if not backup_base.exists():
        print(f"No backups found for {game_slug}")
        return
    
    backups = sorted(backup_base.iterdir(), reverse=True)
    if not backups:
        print(f"No backups found for {game_slug}")
        return
    
    print(f"\nAvailable backups for {game_slug}:")
    for backup in backups:
        print(f"- {backup.name}")

def initialize_from_template(game_slug: str, source_dir: Optional[Path] = None) -> None:
    """Initialize game data from template or source directory"""
    print(f"\nInitializing {game_slug} data...")
    
    # Determine source directory
    if source_dir:
        data_dir = source_dir
        print(f"Using source directory: {data_dir}")
    else:
        data_dir = BASE_DIR / "initial_data" / game_slug / "src" / "data"
        print(f"Using template directory: {data_dir}")
    
    if not data_dir.exists():
        print(f"No data found at {data_dir}")
        return
    
    db_paths = get_database_paths(game_slug)
    
    # Define file mappings with correct case
    file_mappings = {
        'asset': {
            'source': 'AssetDatabase.json',
            'json': db_paths['asset']['json'],
            'lua': db_paths['asset']['lua']
        },
        'npc': {
            'source': 'NPCDatabase.json',
            'json': db_paths['npc']['json'],
            'lua': db_paths['npc']['lua']
        }
    }
    
    # First copy JSON files
    for db_type, paths in file_mappings.items():
        source_file = data_dir / paths['source']
        if source_file.exists():
            print(f"Reading {db_type} data from: {source_file}")
            try:
                with open(source_file, 'r') as f:
                    data = json.load(f)
                    print(f"Found {len(data.get(db_type + 's', []))} {db_type}s in source file")
            except Exception as e:
                print(f"Error reading source file {source_file}: {e}")
                continue
            
            # Create target directory if it doesn't exist
            paths['json'].parent.mkdir(parents=True, exist_ok=True)
            
            # Copy JSON file
            print(f"Copying to: {paths['json']}")
            shutil.copy2(source_file, paths['json'])
            
            print(f"Processed {len(data.get(db_type + 's', []))} {db_type}s")
    
    # Import JSON data into database
    print("\nImporting data into database...")
    import_json_to_db(game_slug, data_dir)
    
    # Generate Lua files from database
    print("\nGenerating Lua files...")
    generate_lua_from_db(game_slug, 'asset')
    generate_lua_from_db(game_slug, 'npc')

def create_backup(game_slug: str) -> None:
    """Create backup of current game data"""
    print(f"\nBacking up {game_slug} data...")
    
    backup_dir = get_backup_dir(game_slug, create_new=True)
    db_paths = get_database_paths(game_slug)
    
    for db_type in ['asset', 'npc']:
        json_file = db_paths[db_type]['json']
        if json_file.exists():
            backup_file = backup_dir / json_file.name
            print(f"Backing up {json_file.name}")
            shutil.copy2(json_file, backup_file)
    
    print(f"Backup created at: {backup_dir}")

def generate_lua_only(game_slug: str) -> None:
    """Generate Lua files directly from database"""
    print(f"\nGenerating Lua files for {game_slug}...")
    
    try:
        generate_lua_from_db(game_slug, 'asset')
        generate_lua_from_db(game_slug, 'npc')
        print("Lua files generated successfully from database")
    except Exception as e:
        print(f"Error generating Lua files: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Manage game data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE_EXAMPLES
    )
    
    parser.add_argument("game_slug", help="Game identifier (e.g., game1)")
    parser.add_argument("--action", choices=[
        "restore", "init", "lua", "backup", "list-backups"
    ], required=True, help="Action to perform")
    parser.add_argument("--help-examples", action="store_true", 
                       help="Show usage examples and exit")
    parser.add_argument("--source-dir", type=Path,
                       help="Source directory containing JSON files to initialize from")
    
    args = parser.parse_args()
    
    if args.help_examples:
        print(USAGE_EXAMPLES)
        return
    
    if args.action == "restore":
        restore_from_backup(args.game_slug)
    elif args.action == "init":
        initialize_from_template(args.game_slug, args.source_dir)
    elif args.action == "lua":
        generate_lua_only(args.game_slug)
    elif args.action == "backup":
        create_backup(args.game_slug)
    elif args.action == "list-backups":
        list_backups(args.game_slug)

if __name__ == "__main__":
    main() 