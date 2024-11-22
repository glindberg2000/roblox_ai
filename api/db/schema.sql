-- Games table
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    asset_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    image_url TEXT,
    tags TEXT DEFAULT '[]',
    FOREIGN KEY (game_id) REFERENCES games(id)
);

-- NPCs table
CREATE TABLE IF NOT EXISTS npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    model TEXT,
    system_prompt TEXT,
    response_radius INTEGER DEFAULT 20,
    spawn_position TEXT,  -- JSON object
    abilities TEXT,  -- JSON array
    game_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Insert default game
INSERT OR IGNORE INTO games (title, slug, description) 
VALUES ('Default Game', 'default-game', 'The default game instance');
