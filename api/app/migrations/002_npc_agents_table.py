import sqlite3
import logging
from datetime import datetime
from ..config import SQLITE_DB_PATH
from ..database import get_db

logger = logging.getLogger("roblox_app")

def check_migration_safety():
    """Check if it's safe to run the migration"""
    with get_db() as db:
        # Check if migration was already run
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='agent_mappings'
        """)
        if cursor.fetchone():
            raise Exception("Migration appears to have already been run (agent_mappings table exists)")
        
        return True

def migrate_npc_agents():
    """Create npc_agents table"""
    logger.info("Starting npc_agents table migration")
    
    # Add safety check
    check_migration_safety()
    
    with get_db() as db:
        try:
            # Start transaction
            db.execute('BEGIN')
            
            # Create npc_agents table
            logger.info("Creating npc_agents table")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS agent_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    npc_id INTEGER NOT NULL,
                    participant_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL DEFAULT 'letta',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (npc_id) REFERENCES npcs(id)
                );

                -- Add index for faster lookups
                CREATE INDEX IF NOT EXISTS idx_agent_mapping 
                ON agent_mappings(npc_id, participant_id, agent_type);
            """)
            
            db.commit()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

def rollback_migration():
    """Rollback the migration"""
    with get_db() as db:
        try:
            db.execute('BEGIN')
            logger.info("Dropping agent mapping index")
            db.execute('DROP INDEX IF EXISTS idx_agent_mapping')
            
            logger.info("Dropping agent_mappings table")
            db.execute('DROP TABLE IF EXISTS agent_mappings')
            
            db.commit()
            logger.info("Rollback completed successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"Rollback failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        migrate_npc_agents()
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
        exit(1) 