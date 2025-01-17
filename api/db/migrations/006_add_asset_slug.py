def migrate(db):
    """Add slug column to assets table if it doesn't exist"""
    print("Checking/adding slug column to assets table...")
    
    try:
        # First check if column exists
        cursor = db.execute("PRAGMA table_info(assets)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'slug' in columns:
            print("✓ Slug column already exists, skipping")
            return
            
        # Add column if it doesn't exist
        db.execute("""
            ALTER TABLE assets 
            ADD COLUMN slug TEXT;
        """)
        
        db.commit()
        print("✓ Successfully added slug column")
        
    except Exception as e:
        print(f"! Failed to handle slug column: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """No rollback needed since we check for existence"""
    pass 