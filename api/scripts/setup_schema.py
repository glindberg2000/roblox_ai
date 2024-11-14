#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Get absolute path to api directory
api_path = Path(__file__).parent.parent.absolute()
db_dir = api_path / "db"
schema_path = db_dir / "schema.sql"

# Create schema.sql
schema = """-- Games table
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    type TEXT,
    tags JSON,
    game_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id)
);

-- NPCs table
CREATE TABLE IF NOT EXISTS npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id TEXT UNIQUE NOT NULL,
    asset_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    model TEXT,
    system_prompt TEXT,
    response_radius INTEGER DEFAULT 20,
    spawn_position JSON,
    abilities JSON,
    short_term_memory JSON,
    game_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (game_id) REFERENCES games(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assets_game_id ON assets(game_id);
CREATE INDEX IF NOT EXISTS idx_npcs_game_id ON npcs(game_id);
CREATE INDEX IF NOT EXISTS idx_npcs_asset_id ON npcs(asset_id);
"""

def setup_schema():
    """Create schema.sql file"""
    try:
        print(f"Creating schema at: {schema_path}")
        
        # Create db directory if it doesn't exist
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Write schema to file
        with open(schema_path, 'w') as f:
            f.write(schema)
            
        print("Schema created successfully!")
        
    except Exception as e:
        print(f"Error creating schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_schema() 