def migrate(db):
    """Add slug trigger for automatic slug generation"""
    print("Adding asset slug trigger...")
    
    try:
        # First check if trigger exists
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name='generate_asset_slug_insert'
        """)
        
        if cursor.fetchone():
            print("✓ Slug trigger already exists, skipping")
            return
            
        # Create trigger for new rows
        db.execute("""
            CREATE TRIGGER IF NOT EXISTS generate_asset_slug_insert
            AFTER INSERT ON assets
            BEGIN
                UPDATE assets 
                SET slug = LOWER(
                    REPLACE(
                        REPLACE(
                            REPLACE(NEW.name, ' ', '_'),
                            "'", ''
                        ),
                        '-', '_'
                    )
                )
                WHERE id = NEW.id;
            END;
        """)
        
        db.commit()
        print("✓ Successfully added slug trigger")
        
    except Exception as e:
        print(f"! Failed to add slug trigger: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """Remove the trigger"""
    try:
        db.execute("DROP TRIGGER IF EXISTS generate_asset_slug_insert")
        db.commit()
    except Exception as e:
        print(f"! Failed to remove trigger: {str(e)}")
        db.rollback()
        raise 