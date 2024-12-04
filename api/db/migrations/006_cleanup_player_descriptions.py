def migrate(db):
    """Clean up player_descriptions table schema"""
    print("Cleaning up player_descriptions table...")
    
    try:
        # Create new table with clean schema
        db.execute("""
            CREATE TABLE player_descriptions_new (
                player_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Copy data
        db.execute("""
            INSERT INTO player_descriptions_new 
            SELECT player_id, description, display_name, created_at, updated_at
            FROM player_descriptions;
        """)
        
        # Drop old table and rename new one
        db.execute("DROP TABLE player_descriptions;")
        db.execute("ALTER TABLE player_descriptions_new RENAME TO player_descriptions;")
        
        db.commit()
        print("✓ Successfully cleaned up player_descriptions table")
        
    except Exception as e:
        print(f"! Failed to clean up table: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """No rollback needed for schema cleanup"""
    pass 