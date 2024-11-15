from pathlib import Path
import json

def create_game_directory(game_slug: str):
    """Create the standard game directory structure."""
    game_path = Path("games") / game_slug
    
    # Create main directories
    directories = [
        "src/assets/npcs",
        "src/data",
        "src/shared/modules"
    ]
    
    for dir_path in directories:
        (game_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create initial database files
    create_empty_database_files(game_path / "src/data")
    
    # Create default.project.json
    create_rojo_project_file(game_path)

def create_empty_database_files(data_path: Path):
    """Create empty database files for a new game."""
    empty_db = {"assets": [], "npcs": []}
    
    for filename in ["AssetDatabase.json", "NPCDatabase.json"]:
        with open(data_path / filename, "w") as f:
            json.dump(empty_db, f, indent=2) 