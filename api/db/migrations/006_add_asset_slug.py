def migrate(db):
    """Add slug column to assets table"""
    print("Adding slug column to assets table...")
    
    try:
        # Add slug column
        db.execute("""
            ALTER TABLE assets 
            ADD COLUMN slug TEXT;
        """)

        # Update existing assets with generated slugs
        db.execute("""
            UPDATE assets 
            SET slug = LOWER(
                REPLACE(
                    REPLACE(
                        REPLACE(name, ' ', '_'),
                        "'", ''
                    ),
                    '-', '_'
                )
            )
            WHERE slug IS NULL;
        """)

        db.commit()
        print("✓ Successfully added and populated slug column")
        
    except Exception as e:
        print(f"! Failed to add slug column: {str(e)}")
        db.rollback()
        raise 