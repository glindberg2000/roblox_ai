CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check if game_id column exists before adding it
SELECT CASE 
    WHEN COUNT(*) = 0 THEN
        'ALTER TABLE items ADD COLUMN game_id INTEGER REFERENCES games(id);'
    ELSE
        'SELECT 1;'
END as sql_to_run
FROM pragma_table_info('items')
WHERE name = 'game_id';

-- Check if game_id column exists in categories before adding it
SELECT CASE 
    WHEN COUNT(*) = 0 THEN
        'ALTER TABLE categories ADD COLUMN game_id INTEGER REFERENCES games(id);'
    ELSE
        'SELECT 1;'
END as sql_to_run
FROM pragma_table_info('categories')
WHERE name = 'game_id';

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_items_game_id ON items(game_id);
CREATE INDEX IF NOT EXISTS idx_categories_game_id ON categories(game_id);
