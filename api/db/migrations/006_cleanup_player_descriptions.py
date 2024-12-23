def migrate(db):
    """Clean up player_descriptions table schema"""
    print("Cleaning up player_descriptions table...")
    
    try:
        # First, check current table structure
        cursor = db.execute("PRAGMA table_info(player_descriptions)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Create new table with clean schema
        db.execute("""
            CREATE TABLE IF NOT EXISTS player_descriptions_new (
                player_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                display_name TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Build dynamic INSERT based on existing columns
        existing_columns = ", ".join(col for col in columns if col in [
            "player_id", "description", "display_name", "updated_at"
        ])
        
        insert_sql = f"""
            INSERT INTO player_descriptions_new ({existing_columns})
            SELECT {existing_columns}
            FROM player_descriptions;
        """
        print(f"Running SQL: {insert_sql}")
        db.execute(insert_sql)
        
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