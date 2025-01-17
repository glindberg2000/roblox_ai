-- Only add slug column if it doesn't exist
SELECT CASE 
    WHEN COUNT(*) = 0 THEN
        'ALTER TABLE assets ADD COLUMN slug TEXT;'
    ELSE
        'SELECT 1;'
END as sql_to_run
FROM pragma_table_info('assets')
WHERE name = 'slug';

-- Create trigger for new rows
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

-- Create trigger for updates to name
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

-- Generate slugs for existing assets
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