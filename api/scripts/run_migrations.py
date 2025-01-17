# api/scripts/run_migrations.py

import sys
import argparse
from pathlib import Path
from db.migrations import run_migrations, rollback_migration

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", help="Migration name to rollback")
    parser.add_argument("--db-path", default="db/game_data.db", 
                       help="Path to database file")
    args = parser.parse_args()
    
    # Ensure db directory exists
    db_dir = Path(args.db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    if args.rollback:
        rollback_migration(args.rollback, db_path=args.db_path)
    else:
        run_migrations(db_path=args.db_path)

if __name__ == "__main__":
    main()