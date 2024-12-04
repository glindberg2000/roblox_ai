# api/db/migrations/005_add_player_display_name.py

def migrate(db):
    """Add display_name column to player_descriptions table"""
    print("Adding display_name column to player_descriptions table...")
    
    try:
        db.execute("""
            ALTER TABLE player_descriptions 
            ADD COLUMN display_name TEXT;
        """)
        db.commit()
        print("✓ Successfully added display_name column")
        
    except Exception as e:
        print(f"! Failed to add display_name column: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """Remove display_name column from player_descriptions table"""
    print("Rolling back display_name column addition...")
    
    try:
        # SQLite doesn't support DROP COLUMN, so we need to:
        # 1. Create new table
        # 2. Copy data
        # 3. Drop old table
        # 4. Rename new table
        
        db.execute("""
            CREATE TABLE player_descriptions_new (
                player_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        db.execute("""
            INSERT INTO player_descriptions_new 
            SELECT player_id, description, updated_at 
            FROM player_descriptions;
        """)
        
        db.execute("DROP TABLE player_descriptions;")
        db.execute("ALTER TABLE player_descriptions_new RENAME TO player_descriptions;")
        
        db.commit()
        print("✓ Successfully removed display_name column")
        
    except Exception as e:
        print(f"! Failed to roll back display_name column: {str(e)}")
        db.rollback()
        raise