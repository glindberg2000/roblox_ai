import os
import shutil
from pathlib import Path
import json

class GameTemplate:
    def __init__(self, template_path=None):
        self.template_path = Path(template_path) if template_path else Path(__file__).parent.parent / "templates" / "game_template"
        self.required_dirs = [
            "src/client",
            "src/server",
            "src/shared",
            "src/data",
            "src/services",
            "src/config",
            "src/debug"
        ]
        self.required_files = [
            "default.project.json",
            "src/init.lua",
            "src/config/GameConfig.lua",
            "src/data/NPCDatabase.lua"
        ]

    def validate_template(self):
        """Validate that template has all required structure"""
        missing = []
        
        # Check directories
        for dir_path in self.required_dirs:
            if not (self.template_path / dir_path).exists():
                missing.append(f"Directory: {dir_path}")
                
        # Check files
        for file_path in self.required_files:
            if not (self.template_path / file_path).exists():
                missing.append(f"File: {file_path}")
                
        return len(missing) == 0, missing

    def clone_game(self, game_id, destination_path=None):
        """Clone template to create new game"""
        if destination_path:
            dest = Path(destination_path)
        else:
            dest = Path(__file__).parent.parent / "games" / str(game_id)
            
        # Validate template first
        is_valid, missing = self.validate_template()
        if not is_valid:
            raise ValueError(f"Invalid template. Missing:\n" + "\n".join(missing))
            
        # Create destination if it doesn't exist
        dest.mkdir(parents=True, exist_ok=True)
        
        # Copy template contents
        self._copy_template(dest)
        
        # Update project configuration
        self._update_project_config(dest, game_id)
        
        return dest

    def _copy_template(self, destination):
        """Copy template contents to destination"""
        def _ignore_patterns(path, names):
            return [n for n in names if n.startswith('.') or n.startswith('__')]
            
        # Copy everything except ignored patterns
        shutil.copytree(self.template_path, destination, dirs_exist_ok=True, ignore=_ignore_patterns)

    def _update_project_config(self, game_path, game_id):
        """Update project configuration with game-specific settings"""
        config_path = game_path / "default.project.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Update game-specific configuration
            config["name"] = f"game_{game_id}"
            config["tree"]["$className"] = "DataModel"
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

def create_game(game_id, template_path=None, destination_path=None):
    """Helper function to create a new game from template"""
    template = GameTemplate(template_path)
    game_path = template.clone_game(game_id, destination_path)
    print(f"Game {game_id} created at {game_path}")
    return game_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create a new game from template')
    parser.add_argument('game_id', help='Game ID or name')
    parser.add_argument('--template', help='Custom template path')
    parser.add_argument('--destination', help='Custom destination path')
    
    args = parser.parse_args()
    create_game(args.game_id, args.template, args.destination) 