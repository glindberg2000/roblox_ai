import sqlite3
import json
import logging
from pathlib import Path
from ..config import SQLITE_DB_PATH
from ..database import get_db

logger = logging.getLogger("roblox_app")

def check_migration_safety():
    """Check if it's safe to run the migration"""
    with get_db() as db:
        # Check if migration was already run
        cursor = db.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='npcs' 
            AND sql LIKE '%spawn_x%'
        """)
        if cursor.fetchone():
            raise Exception("Migration appears to have already been run (spawn_x column exists)")
        
        # Count NPCs to migrate
        cursor = db.execute("SELECT COUNT(*) as count FROM npcs")
        count = cursor.fetchone()['count']
        logger.info(f"Found {count} NPCs to migrate")
        
        return True

def migrate_spawn_positions():
    """Add and populate spawn position columns"""
    logger.info("Starting spawn position migration")
    
    # Add safety check
    check_migration_safety()
    
    with get_db() as db:
        try:
            # Start transaction
            db.execute('BEGIN')
            
            # 1. Add new columns with defaults
            logger.info("Adding new spawn position columns")
            db.executescript("""
                ALTER TABLE npcs ADD COLUMN spawn_x REAL DEFAULT 0;
                ALTER TABLE npcs ADD COLUMN spawn_y REAL DEFAULT 5;
                ALTER TABLE npcs ADD COLUMN spawn_z REAL DEFAULT 0;
            """)
            
            # 2. Get all NPCs with spawn positions
            logger.info("Fetching existing NPCs")
            npcs = db.execute("SELECT id, spawn_position FROM npcs").fetchall()
            
            # 3. Migrate existing data
            for npc in npcs:
                try:
                    # Parse existing JSON
                    pos = json.loads(npc['spawn_position'] or '{"x":0,"y":5,"z":0}')
                    
                    logger.info(f"Migrating NPC {npc['id']} position: {pos}")
                    
                    # Update with individual columns
                    db.execute("""
                        UPDATE npcs 
                        SET spawn_x = ?, spawn_y = ?, spawn_z = ?
                        WHERE id = ?
                    """, (
                        float(pos.get('x', 0)),
                        float(pos.get('y', 5)),
                        float(pos.get('z', 0)),
                        npc['id']
                    ))
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON for NPC {npc['id']}, using defaults")
                    # Handle invalid JSON
                    db.execute("""
                        UPDATE npcs 
                        SET spawn_x = 0, spawn_y = 5, spawn_z = 0
                        WHERE id = ?
                    """, (npc['id'],))
                except Exception as e:
                    logger.error(f"Error migrating NPC {npc['id']}: {str(e)}")
                    raise
            
            db.commit()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        migrate_spawn_positions()
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        exit(1) 