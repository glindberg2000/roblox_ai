import shutil
import os
from datetime import datetime
from pathlib import Path

def backup_database():
    """Create a backup of the SQLite database and JSON files"""
    try:
        # Setup paths
        api_dir = Path(__file__).parent.parent
        backup_dir = api_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create timestamp for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup SQLite database
        db_path = api_dir / "db" / "game_data.db"
        if db_path.exists():
            db_backup = backup_dir / f"game_data_{timestamp}.db"
            shutil.copy2(db_path, db_backup)
            print(f"Database backed up to: {db_backup}")
            
        # Backup JSON files
        data_dir = api_dir.parent / "src" / "data"
        if data_dir.exists():
            json_backup_dir = backup_dir / f"json_{timestamp}"
            json_backup_dir.mkdir(exist_ok=True)
            
            for file in data_dir.glob("*.json"):
                shutil.copy2(file, json_backup_dir / file.name)
            for file in data_dir.glob("*.lua"):
                shutil.copy2(file, json_backup_dir / file.name)
            
            print(f"JSON/Lua files backed up to: {json_backup_dir}")
            
        print("Backup completed successfully!")
        
    except Exception as e:
        print(f"Error during backup: {e}")
        raise

if __name__ == "__main__":
    backup_database() 