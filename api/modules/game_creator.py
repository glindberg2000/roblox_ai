from pathlib import Path
from typing import Optional, Dict
import shutil
import json

class GameCreator:
    def __init__(self, template_root: str = None):
        self.template_root = Path(template_root) if template_root else Path(__file__).parent.parent.parent / "templates" / "game_template"
        self.required_structure = {
            "directories": [
                "src/client",
                "src/server",
                "src/shared",
                "src/data",
                "src/services",
                "src/config",
                "src/debug"
            ],
            "files": [
                "default.project.json",
                "src/init.lua",
                "src/config/GameConfig.lua",
                "src/data/NPCDatabase.lua"
            ]
        }

    async def create_game(self, 
                         game_id: str, 
                         config: Dict = None, 
                         destination: Optional[str] = None) -> Path:
        """
        Create a new game from template
        
        Args:
            game_id: Unique identifier for the game
            config: Optional configuration overrides
            destination: Optional destination path
        """
        # Determine destination path
        dest_path = Path(destination) if destination else Path("games") / str(game_id)
        dest_path.mkdir(parents=True, exist_ok=True)

        # Validate template
        await self._validate_template()

        # Copy template
        await self._copy_template(dest_path)

        # Update configuration
        if config:
            await self._update_config(dest_path, game_id, config)

        return dest_path

    async def _validate_template(self):
        """Validate template structure exists"""
        missing = []
        
        for dir_path in self.required_structure["directories"]:
            if not (self.template_root / dir_path).exists():
                missing.append(f"Directory: {dir_path}")
                
        for file_path in self.required_structure["files"]:
            if not (self.template_root / file_path).exists():
                missing.append(f"File: {file_path}")
                
        if missing:
            raise ValueError(f"Invalid template structure. Missing:\n" + "\n".join(missing))

    async def _copy_template(self, destination: Path):
        """Copy template files to destination"""
        def _ignore_patterns(path, names):
            return [n for n in names if n.startswith('.') or n.startswith('__')]
            
        shutil.copytree(self.template_root, destination, 
                       dirs_exist_ok=True, 
                       ignore=_ignore_patterns)

    async def _update_config(self, game_path: Path, game_id: str, config: Dict):
        """Update game configuration"""
        config_path = game_path / "default.project.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                base_config = json.load(f)
            
            # Update with provided config
            base_config.update({
                "name": f"game_{game_id}",
                **config
            })
            
            with open(config_path, 'w') as f:
                json.dump(base_config, f, indent=2) 