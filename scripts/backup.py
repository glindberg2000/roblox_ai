import shutil
import os
from datetime import datetime
from pathlib import Path

def backup_private():
    """Backup private data that isn't in Git"""
    try:
        # Setup paths
        root_dir = Path(__file__).parent.parent
        private_backup_dir = root_dir.parent / "roblox_private_assets"
        
        # Create private backup directories
        private_backup_dir.mkdir(exist_ok=True)
        (private_backup_dir / "databases").mkdir(exist_ok=True)
        (private_backup_dir / "assets").mkdir(exist_ok=True)
        (private_backup_dir / "config").mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Backup SQLite database
        db_path = root_dir / "api" / "db" / "game_data.db"
        if db_path.exists():
            shutil.copy2(db_path, private_backup_dir / "databases" / "game_data.db")
            print(f"Database backed up to private storage")
            
        # 2. Backup JSON/Lua files
        data_dir = root_dir / "src" / "data"
        if data_dir.exists():
            for file in data_dir.glob("*.{json,lua,db,sqlite,sqlite3}"):
                shutil.copy2(file, private_backup_dir / "databases" / file.name)
            print(f"Data files backed up to private storage")
            
        # 3. Backup assets
        assets_dir = root_dir / "api" / "storage"
        if assets_dir.exists():
            for item in assets_dir.glob("**/*"):
                if item.is_file():
                    rel_path = item.relative_to(assets_dir)
                    dest_path = private_backup_dir / "assets" / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
            print(f"Assets backed up to private storage")
            
        # 4. Backup config
        env_file = root_dir / "api" / ".env"
        if env_file.exists():
            shutil.copy2(env_file, private_backup_dir / "config" / ".env")
            print(f"Config backed up to private storage")
            
        print("Private data backup completed successfully!")
        
    except Exception as e:
        print(f"Error during backup: {e}")
        raise

if __name__ == "__main__":
    backup_private() 