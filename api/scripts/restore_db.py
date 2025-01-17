import shutil
import os
from pathlib import Path
import sys

def restore_database(backup_path: str = None):
    """Restore database from backup"""
    try:
        api_dir = Path(__file__).parent.parent
        backup_dir = api_dir / "backups"
        
        if not backup_path:
            # Get latest backup
            db_backups = list(backup_dir.glob("game_data_*.db"))
            if not db_backups:
                print("No backups found!")
                return
            backup_path = str(max(db_backups, key=os.path.getctime))
        
        # Restore SQLite database
        db_path = api_dir / "db" / "game_data.db"
        shutil.copy2(backup_path, db_path)
        print(f"Database restored from: {backup_path}")
        
        # Get corresponding JSON backup
        timestamp = backup_path.split("game_data_")[-1].replace(".db", "")
        json_backup_dir = backup_dir / f"json_{timestamp}"
        
        if json_backup_dir.exists():
            data_dir = api_dir.parent / "src" / "data"
            for file in json_backup_dir.glob("*.*"):
                shutil.copy2(file, data_dir / file.name)
            print(f"JSON/Lua files restored from: {json_backup_dir}")
        
        print("Restore completed successfully!")
        
    except Exception as e:
        print(f"Error during restore: {e}")
        raise

if __name__ == "__main__":
    backup_path = sys.argv[1] if len(sys.argv) > 1 else None
    restore_database(backup_path) 