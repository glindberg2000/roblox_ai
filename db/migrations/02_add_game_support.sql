CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Modify items table to include game_id
ALTER TABLE items ADD COLUMN game_id INTEGER;
ALTER TABLE items ADD FOREIGN KEY (game_id) REFERENCES games(id); 