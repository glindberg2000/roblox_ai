-- Add slug column
ALTER TABLE assets ADD COLUMN slug TEXT;

-- Update existing assets with generated slugs
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