import json
import shutil
from pathlib import Path
from api.app.config import BASE_DIR
import os

TEMPLATE_DIR = BASE_DIR / "templates" / "game_template"
GAME1_DIR = Path(os.path.dirname(BASE_DIR)) / "games" / "game1"

def create_game_template():
    """Create the base game template structure by copying from game1"""
    print(f"Creating game template in: {TEMPLATE_DIR}")
    
    # Clear existing template if it exists
    if TEMPLATE_DIR.exists():
        shutil.rmtree(TEMPLATE_DIR)
    
    # Create template directory
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copy entire structure from game1
    print(f"Copying structure from: {GAME1_DIR}")
    
    # Copy src directory structure
    shutil.copytree(GAME1_DIR / "src", TEMPLATE_DIR / "src", dirs_exist_ok=True)
    
    # Empty the database files but keep structure
    db_files = {
        "src/data/AssetDatabase.json": {"assets": []},
        "src/data/NPCDatabase.json": {"npcs": []},
        "src/data/AssetDatabase.lua": "return {\n    assets = {}\n}\n",
        "src/data/NPCDatabase.lua": "return {\n    npcs = {}\n}\n"
    }
    
    for file_path, content in db_files.items():
        file = TEMPLATE_DIR / file_path
        if isinstance(content, dict):
            with open(file, 'w') as f:
                json.dump(content, f, indent=4)
        else:
            with open(file, 'w') as f:
                f.write(content)
    
    # Copy and modify project.json
    project_json_path = GAME1_DIR / "default.project.json"
    if project_json_path.exists():
        with open(project_json_path, 'r') as f:
            project_data = json.load(f)
        
        # Update name to template
        project_data['name'] = "GameTemplate"
        
        # Save to template directory
        with open(TEMPLATE_DIR / "default.project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
    
    print("Game template created successfully!")
    print(f"Template location: {TEMPLATE_DIR}")

if __name__ == "__main__":
    create_game_template() 