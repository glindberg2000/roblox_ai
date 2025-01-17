import shutil
import os
from pathlib import Path
import sys

def restore_private():
    """Restore private data after Git checkout"""
    try:
        root_dir = Path(__file__).parent.parent
        private_backup_dir = root_dir.parent / "roblox_private_assets"
        
        # 1. Restore database
        db_src = private_backup_dir / "databases" / "game_data.db"
        if db_src.exists():
            db_dest = root_dir / "api" / "db" / "game_data.db"
            db_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_src, db_dest)
            print(f"Database restored from private backup")
        
        # 2. Restore data files
        data_dir = root_dir / "src" / "data"
        data_dir.mkdir(exist_ok=True)
        for file in (private_backup_dir / "databases").glob("*.*"):
            shutil.copy2(file, data_dir / file.name)
        print(f"Data files restored from private backup")
        
        # 3. Restore assets
        assets_dir = root_dir / "api" / "storage"
        if assets_dir.exists():
            shutil.rmtree(assets_dir)
        shutil.copytree(private_backup_dir / "assets", assets_dir)
        print(f"Assets restored from private backup")
        
        # 4. Restore config
        env_file = private_backup_dir / "config" / ".env"
        if env_file.exists():
            shutil.copy2(env_file, root_dir / "api" / ".env")
            print(f"Config restored from private backup")
            
        print("Private data restore completed successfully!")
        
    except Exception as e:
        print(f"Error during restore: {e}")
        raise

if __name__ == "__main__":
    restore_private() 