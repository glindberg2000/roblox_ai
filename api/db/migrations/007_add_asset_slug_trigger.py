def migrate(db):
    """Add slug column and trigger for automatic slug generation"""
    print("Adding slug column and trigger...")
    
    try:
        # Add slug column if it doesn't exist
        db.execute("""
            ALTER TABLE assets 
            ADD COLUMN slug TEXT;
        """)

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

        # Create trigger for updates to name
        db.execute("""
            CREATE TRIGGER IF NOT EXISTS generate_asset_slug_update
            AFTER UPDATE OF name ON assets
            WHEN NEW.name != OLD.name
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

        # Generate slugs for existing assets
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
        print("✓ Successfully added slug column and triggers")
        
    except Exception as e:
        print(f"! Failed to add slug column and triggers: {str(e)}")
        db.rollback()
        raise 