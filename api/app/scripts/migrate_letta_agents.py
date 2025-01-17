from ..database import get_db
import logging

logger = logging.getLogger("roblox_app")

def migrate_letta_agents():
    """Move agent mappings to dedicated table"""
    with get_db() as db:
        try:
            # Create new table
            print("Creating npc_agents table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS npc_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    npc_id TEXT NOT NULL,
                    participant_id TEXT NOT NULL,
                    letta_agent_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(npc_id, participant_id)
                )
            """)

            db.commit()
            print("Migration completed successfully!")
            
            # Verify table exists and has correct schema
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='npc_agents'")
            if not cursor.fetchone():
                raise Exception("Migration failed: npc_agents table not created")
            
            print("\nVerifying table schema:")
            cursor = db.execute("PRAGMA table_info(npc_agents)")
            for col in cursor.fetchall():
                print(f"Column: {col['name']}, Type: {col['type']}")
            
        except Exception as e:
            db.rollback()
            print(f"Error during migration: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_letta_agents() 