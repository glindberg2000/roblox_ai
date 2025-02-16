def migrate(db):
    """Add enabled column to npcs table"""
    print("Adding enabled column to npcs table...")
    
    try:
        # Add enabled column with default value of True
        db.execute("""
            ALTER TABLE npcs 
            ADD COLUMN enabled BOOLEAN DEFAULT TRUE;
        """)
        
        # Update any existing NPCs to be enabled by default
        db.execute("""
            UPDATE npcs 
            SET enabled = TRUE 
            WHERE enabled IS NULL;
        """)
        
        db.commit()
        print("✓ Successfully added enabled column")
        
    except Exception as e:
        print(f"! Failed to add enabled column: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """No rollback needed for SQLite column additions"""
    pass 