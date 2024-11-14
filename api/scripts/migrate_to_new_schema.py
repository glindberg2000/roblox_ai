import sqlite3
import json
from pathlib import Path

def init_schema(db):
    """Initialize database schema"""
    print("Initializing schema...")
    db.executescript("""
        -- Games table
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
    """)
    print("Schema initialized")

def load_json_file(path):
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def migrate_to_new_schema():
    """Migrate data from JSON files to new schema"""
    db_path = Path(__file__).parent.parent / "db" / "game_data.db"
    root_dir = Path(__file__).parent.parent.parent
    
    # JSON file paths
    asset_json = root_dir / "src" / "data" / "AssetDatabase.json"
    npc_json = root_dir / "src" / "data" / "NPCDatabase.json"
    
    print(f"Loading assets from: {asset_json}")
    print(f"Loading NPCs from: {npc_json}")
    
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        
        print("Starting migration to new schema...")
        
        # Initialize schema first
        init_schema(db)
        
        # First, ensure we have a default game
        db.execute("""
            INSERT OR IGNORE INTO games (name, slug, description)
            VALUES (?, ?, ?)
        """, ("Game1", "game1", "Default game"))
        db.commit()
        
        game_id = db.execute("SELECT id FROM games WHERE slug = 'game1'").fetchone()['id']
        
        # Load JSON data
        asset_data = load_json_file(asset_json)
        npc_data = load_json_file(npc_json)
        
        # Track NPC asset IDs
        npc_asset_ids = set()
        for npc in npc_data.get("npcs", []):
            # Remove any npc_ prefix if it exists
            clean_asset_id = npc["assetId"].replace("npc_", "")
            npc_asset_ids.add(clean_asset_id)
        
        print(f"\nFound NPC asset IDs: {npc_asset_ids}")
        
        # First, migrate assets
        print("\nMigrating assets...")
        for asset in asset_data.get("assets", []):
            asset_id = asset["assetId"]
            asset_type = "npc_base" if asset_id in npc_asset_ids else asset.get("type", "unknown")
            tags = asset.get("tags", [])
            if asset_type == "npc_base" and "npc" not in tags:
                tags.append("npc")
            
            db.execute("""
                INSERT OR REPLACE INTO assets (
                    asset_id, name, description, image_url, 
                    type, tags, game_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                asset["name"],
                asset.get("description", ""),
                asset.get("imageUrl", ""),
                asset_type,
                json.dumps(tags),
                game_id
            ))
            print(f"Migrated asset: {asset['name']} (ID: {asset_id}, Type: {asset_type})")
        
        # Then migrate NPCs
        print("\nMigrating NPCs...")
        for npc in npc_data.get("npcs", []):
            # Remove any npc_ prefix if it exists
            clean_asset_id = npc["assetId"].replace("npc_", "")
            
            db.execute("""
                INSERT OR REPLACE INTO npcs (
                    npc_id, asset_id, display_name, model,
                    system_prompt, response_radius, spawn_position,
                    abilities, short_term_memory, game_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                npc["id"],
                clean_asset_id,  # Use clean asset ID
                npc["displayName"],
                npc.get("model", ""),
                npc.get("system_prompt", ""),
                npc.get("responseRadius", 20),
                json.dumps(npc.get("spawnPosition", {})),
                json.dumps(npc.get("abilities", [])),
                json.dumps(npc.get("shortTermMemory", {})),
                game_id
            ))
            print(f"Migrated NPC: {npc['displayName']} -> Asset: {clean_asset_id}")
        
        db.commit()
        
        # Verify migration
        assets_count = db.execute("SELECT COUNT(*) as count FROM assets").fetchone()['count']
        npcs_count = db.execute("SELECT COUNT(*) as count FROM npcs").fetchone()['count']
        
        print(f"\nMigration complete!")
        print(f"Assets migrated: {assets_count}")
        print(f"NPCs migrated: {npcs_count}")
        
        # Check relationships
        print("\nVerifying NPC-Asset relationships:")
        cursor = db.execute("""
            SELECT n.npc_id, n.display_name, n.asset_id, a.name as asset_name, a.type
            FROM npcs n
            LEFT JOIN assets a ON n.asset_id = a.asset_id
            ORDER BY n.display_name
        """)
        for rel in cursor.fetchall():
            if rel['asset_name'] is None:
                print(f"WARNING: Orphaned NPC {rel['display_name']} -> missing asset {rel['asset_id']}")
            else:
                print(f"OK: NPC {rel['display_name']} -> Asset {rel['asset_name']} (Type: {rel['type']})")

if __name__ == "__main__":
    migrate_to_new_schema() 