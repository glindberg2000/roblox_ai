#!/usr/bin/env python3

import shutil
from pathlib import Path

def reorganize_files():
    """Reorganize files into the correct game1 structure"""
    try:
        print("Starting file reorganization...")
        
        # Setup paths
        root_dir = Path(__file__).parent.parent.parent
        game1_dir = root_dir / "games" / "game1"
        shared_dir = root_dir / "shared"
        
        # Create game1 directory structure
        game1_src = game1_dir / "src"
        game1_shared = game1_src / "shared"
        game1_modules = game1_shared / "modules"
        
        # Create directories
        for dir_path in [game1_src, game1_shared, game1_modules]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Move shared modules into game1
        if shared_dir.exists():
            if (shared_dir / "modules").exists():
                for file in (shared_dir / "modules").glob("*.lua"):
                    dest = game1_modules / file.name
                    print(f"Moving {file} to {dest}")
                    shutil.copy2(file, dest)
            
            # Remove old shared directory
            print(f"Removing old shared directory: {shared_dir}")
            shutil.rmtree(shared_dir)
        
        print("\nVerifying structure...")
        print(f"Game1 modules directory: {game1_modules}")
        if game1_modules.exists():
            print("Files found:")
            for file in game1_modules.glob("*"):
                print(f"  {file.name}")
        
        print("\nReorganization complete!")
        
    except Exception as e:
        print(f"Error during reorganization: {e}")
        raise

if __name__ == "__main__":
    reorganize_files() 