import shutil
from pathlib import Path
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateManager:
    def __init__(self, source_path=None):
        # Allow source path to be specified or use default
        if source_path:
            self.source_path = Path(source_path)
        else:
            # Try to find the source directory
            possible_paths = [
                Path.home() / "dev" / "roblox_ai" / "src",
                Path.home() / "dev" / "roblox-ai" / "src",
                Path(__file__).parent.parent.parent / "roblox_ai" / "src"
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.source_path = path
                    break
            else:
                raise FileNotFoundError("Could not find source template directory")
        
        self.target_path = Path(__file__).parent.parent / "games" / "_template" / "src"
        
        logger.info(f"Source path: {self.source_path}")
        logger.info(f"Target path: {self.target_path}")
        
        # List contents of source directory
        if self.source_path.exists():
            logger.info("Source directory contents:")
            self._print_directory_tree(self.source_path)

    def _print_directory_tree(self, path, prefix=""):
        """Print directory tree structure"""
        for item in sorted(path.iterdir()):
            logger.info(f"{prefix}├── {item.name}")
            if item.is_dir():
                self._print_directory_tree(item, prefix + "│   ")

    def _should_copy_file(self, file_path):
        """Check if file should be copied based on extension and name"""
        # Skip backup files
        if file_path.name.endswith('.backup'):
            return False
            
        # For testing, include all game-related files
        valid_extensions = [
            '.lua',    # Scripts
            '.json',   # Config
            '.rbxm',   # Models
            '.rbxmx'   # XML Models
        ]
        
        return file_path.suffix.lower() in valid_extensions

    def copy_template(self):
        """Copy the working template to templates directory"""
        logger.info(f"Copying template from {self.source_path} to {self.target_path}")
        logger.info("Note: Including database and model files for testing purposes")
        
        # Backup existing template if it exists
        template_root = self.target_path.parent
        if template_root.exists():
            backup_path = template_root.parent / "game_template_backup"
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.move(template_root, backup_path)
            logger.info(f"Backed up existing template to {backup_path}")
        
        # Create fresh template directory
        self.target_path.mkdir(parents=True, exist_ok=True)
        
        # Copy project.json if it exists in source root
        source_project = self.source_path.parent / "default.project.json"
        if source_project.exists():
            target_project = self.target_path.parent / "default.project.json"
            shutil.copy2(source_project, target_project)
            logger.info(f"Copied default.project.json from {source_project} to {target_project}")
        else:
            logger.warning("default.project.json not found in source directory")
        
        # Walk through source directory and copy structure
        for source_item in self.source_path.rglob('*'):
            # Calculate relative path from source root
            rel_path = source_item.relative_to(self.source_path)
            target_item = self.target_path / rel_path
            
            if source_item.is_dir():
                # Create directory
                target_item.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {rel_path}")
            elif source_item.is_file() and self._should_copy_file(source_item):
                # Copy file if it's a supported type
                target_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_item, target_item)
                logger.info(f"Copied file: {rel_path}")
        
        logger.info("Template copied successfully")
        logger.info(f"Template location: {self.target_path.parent}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Copy working template to templates directory')
    parser.add_argument('--source', help='Path to source template directory')
    
    args = parser.parse_args()
    manager = TemplateManager(args.source)
    manager.copy_template() 