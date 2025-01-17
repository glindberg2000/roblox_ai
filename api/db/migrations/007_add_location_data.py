def migrate(db):
    """Add location data to assets table"""
    print("Adding location data columns to assets table...")
    
    try:
        # Add columns one by one to handle SQLite limitations
        columns = [
            ("location_data", "TEXT DEFAULT '{}'"),
            ("is_location", "BOOLEAN DEFAULT FALSE"),
            ("position_x", "REAL"),
            ("position_y", "REAL"),
            ("position_z", "REAL"),
            ("aliases", "TEXT DEFAULT '[]'")
        ]
        
        for col_name, col_type in columns:
            try:
                db.execute(f"ALTER TABLE assets ADD COLUMN {col_name} {col_type};")
                print(f"✓ Added column: {col_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Column already exists: {col_name}")
                else:
                    raise
        
        db.commit()
        print("✓ Successfully added location data columns")
        
    except Exception as e:
        print(f"! Failed to add location columns: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """
    Note: SQLite doesn't support DROP COLUMN, 
    so we'd need to recreate the table to remove columns
    """
    print("Rollback not supported for SQLite column additions")
    pass 