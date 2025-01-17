def migrate(db):
    """Create base tables from schema"""
    print("Creating base tables...")
    
    try:
        # Create games table
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ Created games table")
        
        # Create assets table
        db.execute("""
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
        """)
        print("✓ Created assets table")
        
        # Create NPCs table
        db.execute("""
            CREATE TABLE IF NOT EXISTS npcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npc_id TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                model TEXT,
                system_prompt TEXT,
                response_radius INTEGER DEFAULT 20,
                spawn_position TEXT,
                abilities TEXT,
                game_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            );
        """)
        print("✓ Created npcs table")
        
        # Insert default game if not exists
        db.execute("""
            INSERT OR IGNORE INTO games (title, slug, description) 
            VALUES ('Default Game', 'default-game', 'The default game instance');
        """)
        print("✓ Ensured default game exists")
        
        db.commit()
        print("✓ Successfully created base tables")
        
    except Exception as e:
        print(f"! Failed to create base tables: {str(e)}")
        db.rollback()
        raise

def rollback(db):
    """Drop all created tables"""
    try:
        db.execute("DROP TABLE IF EXISTS npcs;")
        db.execute("DROP TABLE IF EXISTS assets;")
        db.execute("DROP TABLE IF EXISTS games;")
        db.commit()
        print("✓ Successfully dropped all tables")
    except Exception as e:
        print(f"! Failed to drop tables: {str(e)}")
        db.rollback()
        raise 