"""Add player descriptions table

This migration adds a table to store AI-generated player avatar descriptions.
"""

def migrate(db):
    """Create player_descriptions table"""
    print("Creating player_descriptions table...")
    
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS player_descriptions (
                player_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        db.commit()
        print("✓ Successfully created player_descriptions table")
        
    except Exception as e:
        print(f"! Failed to create player_descriptions table: {str(e)}")
        db.rollback()
        raise 

def rollback(db):
    """Remove player_descriptions table"""
    print("Removing player_descriptions table...")
    
    try:
        db.execute("DROP TABLE IF EXISTS player_descriptions")
        db.commit()
        print("✓ Successfully removed player_descriptions table")
    except Exception as e:
        print(f"! Failed to remove player_descriptions table: {str(e)}")
        db.rollback()
        raise