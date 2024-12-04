# api/db/migrations/__init__.py

import sqlite3
import os
from importlib import util as importlib_util
from pathlib import Path

def run_migrations(db_path="db/game_data.db"):
    """Run all pending migrations"""
    print(f"Running migrations on {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    # Create migrations table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Get list of applied migrations
    applied = {row[0] for row in conn.execute("SELECT name FROM migrations")}
    
    # Get all migration files
    migrations_dir = Path(__file__).parent
    migration_files = sorted([f for f in migrations_dir.glob("*.py") 
                            if f.stem.startswith("0")])
    
    for migration_file in migration_files:
        name = migration_file.stem
        if name not in applied:
            print(f"\nApplying migration: {name}")
            
            # Import and run migration
            spec = importlib_util.spec_from_file_location(name, migration_file)
            module = importlib_util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            try:
                module.migrate(conn)
                conn.execute("INSERT INTO migrations (name) VALUES (?)", (name,))
                conn.commit()
                print(f"✓ Successfully applied {name}")
            except Exception as e:
                print(f"! Failed to apply {name}: {str(e)}")
                conn.rollback()
                raise
    
    conn.close()

def rollback_migration(migration_name: str, db_path="db/game_data.db"):
    """Rollback a specific migration"""
    print(f"Rolling back migration {migration_name}")
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Check if migration was applied
        result = conn.execute(
            "SELECT name FROM migrations WHERE name = ?", 
            (migration_name,)
        ).fetchone()
        
        if not result:
            print(f"! Migration {migration_name} was not applied")
            return
        
        # Import and run rollback
        migrations_dir = Path(__file__).parent
        migration_file = migrations_dir / f"{migration_name}.py"
        
        if not migration_file.exists():
            print(f"! Migration file {migration_name}.py not found")
            return
            
        spec = importlib_util.spec_from_file_location(migration_name, migration_file)
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run rollback
        module.rollback(conn)
        
        # Remove from migrations table
        conn.execute("DELETE FROM migrations WHERE name = ?", (migration_name,))
        conn.commit()
        
        print(f"✓ Successfully rolled back {migration_name}")
        
    except Exception as e:
        print(f"! Failed to roll back {migration_name}: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()