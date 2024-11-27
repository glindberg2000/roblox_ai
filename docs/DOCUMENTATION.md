# API Documentation

## Directory Structure

```
api/
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── conversation_manager.py
│   ├── dashboard_router.py
│   ├── database.py
│   ├── db.py
│   ├── image_utils.py
│   ├── main.py
│   ├── paths.py
│   ├── routers.py
│   ├── storage.py
│   └── utils.py
├── db
│   ├── migrate.py
│   ├── schema.sql
├── initial_data
│   └── game1
│       └── src
│           └── data
│               ├── AssetDatabase.json
│               └── NPCDatabase.json
├── modules
│   └── game_creator.py
├── routes
│   └── games.py
├── static
│   ├── css
│   │   └── dashboard.css
│   └── js
│       ├── dashboard_new
│       │   ├── abilityConfig.js
│       │   ├── assets.js
│       │   ├── game.js
│       │   ├── games.js
│       │   ├── index.js
│       │   ├── npc.js
│       │   ├── state.js
│       │   ├── ui.js
│       │   └── utils.js
│       ├── abilityConfig.js
│       ├── dashboard.js
│       └── games.js
├── storage
│   ├── assets
│   │   ├── models
│   │   ├── thumbnails
│   ├── avatars
│   ├── default
│   │   ├── assets
│   │   ├── avatars
│   │   └── thumbnails
│   └── thumbnails
├── templates
│   ├── dashboard_new.html
│   ├── npc-edit.html
│   ├── npcs.html
│   └── players.html
├── .env.example
├── init_db.py
├── pytest.ini
├── requirements.txt
├── setup_db.py
├── test_imports.py
└── testimg.py
```

## API Files

### api/test_imports.py

```py
import os
import sys
from pathlib import Path

print(f"Current working directory: {os.getcwd()}")
print(f"Python path before: {sys.path}")

# Add the current directory to Python path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
print(f"Added to path: {current_dir}")
print(f"Python path after: {sys.path}")

try:
    from app.database import init_db
    print("Successfully imported database")
    from app.utils import load_json_database
    print("Successfully imported utils")
except ImportError as e:
    print(f"Import error: {e}") 
```

### api/requirements.txt

```txt
fastapi
uvicorn
python-dotenv
jinja2
aiofiles
python-multipart
requests
pillow
python-slugify

```

### api/setup_db.py

```py
#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    # Now try to import
    from app.database import init_db, get_db
    from app.utils import load_json_database, get_database_paths
    
    print("Successfully imported modules")
    
    def setup_database():
        """Initialize database and migrate data"""
        try:
            print("Initializing database...")
            init_db()
            
            print("Loading JSON data...")
            db_paths = get_database_paths()
            asset_data = load_json_database(db_paths['asset']['json'])
            
            print("Migrating data to SQLite...")
            with get_db() as db:
                # First, count existing items
                cursor = db.execute("SELECT COUNT(*) as count FROM items")
                before_count = cursor.fetchone()["count"]
                print(f"Items in database before migration: {before_count}")
                
                # Migrate assets
                for asset in asset_data.get("assets", []):
                    properties = {
                        "imageUrl": asset.get("imageUrl", ""),
                        "storage_type": asset.get("storage_type", "")
                    }
                    
                    db.execute("""
                        INSERT OR REPLACE INTO items 
                        (item_id, name, description, properties)
                        VALUES (?, ?, ?, ?)
                    """, (
                        asset["assetId"],
                        asset["name"],
                        asset.get("description", ""),
                        json.dumps(properties)
                    ))
                
                db.commit()
                
                # Verify migration
                cursor = db.execute("SELECT COUNT(*) as count FROM items")
                after_count = cursor.fetchone()["count"]
                print(f"Migration completed successfully!")
                print(f"Items in database after migration: {after_count}")
                print(f"Added {after_count - before_count} new items")
                
        except Exception as e:
            print(f"Error during setup: {e}")
            raise

    if __name__ == "__main__":
        setup_database()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure app/database.py and app/utils.py exist and are importable")
    sys.exit(1) 
```

### api/init_db.py

```py
#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path

# Get absolute path to api directory
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    # Import our modules
    from app.database import init_db, get_db
    from app.utils import load_json_database, get_database_paths
    
    print("Successfully imported modules")
    print("Initializing database...")
    init_db()
    
    print("Loading JSON data...")
    db_paths = get_database_paths()
    asset_data = load_json_database(db_paths['asset']['json'])
    
    print("Migrating data to SQLite...")
    with get_db() as db:
        # First, count existing items
        cursor = db.execute("SELECT COUNT(*) as count FROM items")
        before_count = cursor.fetchone()["count"]
        print(f"Items in database before migration: {before_count}")
        
        # Migrate assets
        for asset in asset_data.get("assets", []):
            properties = {
                "imageUrl": asset.get("imageUrl", ""),
                "storage_type": asset.get("storage_type", "")
            }
            
            db.execute("""
                INSERT OR REPLACE INTO items 
                (item_id, name, description, properties)
                VALUES (?, ?, ?, ?)
            """, (
                asset["assetId"],
                asset["name"],
                asset.get("description", ""),
                json.dumps(properties)
            ))
        
        db.commit()
        
        # Verify migration
        cursor = db.execute("SELECT COUNT(*) as count FROM items")
        after_count = cursor.fetchone()["count"]
        print(f"Migration completed successfully!")
        print(f"Items in database after migration: {after_count}")
        print(f"Added {after_count - before_count} new items")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the api directory")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) 
```

### api/testimg.py

```py
import base64
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
# Function to encode the image into base64 format
def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to generate AI description using the gpt-4o-mini model
def generate_ai_description_from_image(image_path: str) -> str:
    # Encode the image into base64
    base64_image = encode_image(image_path)
    
    # Sending the image to the OpenAI API for detailed avatar description
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Using gpt-4o-mini model
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please provide a detailed description of this Roblox avatar. "
                            "Include details about the avatar's clothing, accessories, colors, any unique features, "
                            "and its overall style or theme. The description will be used by NPCs in a game to "
                            "interact with the player based on their appearance."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    }
                ],
            }
        ]
    )

    # Debugging: print the raw response
    print(f"Raw response from OpenAI: {response}")

    # Extract and return the AI-generated description
    try:
        description = response.choices[0].message.content  # Correct attribute access
        return description
    except AttributeError as e:
        # Handle the case where the structure is different or there's an issue
        print(f"Error accessing the response content: {e}")
        return "No description available"

# Add a main section for manual testing
if __name__ == "__main__":
    image_path = "./stored_images/962483389.png"  # Path to the stored image
    print(f"Testing with image: {image_path}")
    
    try:
        description = generate_ai_description_from_image(image_path)
        print(f"AI-Generated Description: {description}")
    except Exception as e:
        print(f"Error generating description: {e}")
```

### api/pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = api/tests
addopts = -v
asyncio_fixture_loop_scope = function
```

### api/app/main.py

```py
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

# Create logger for our app
logger = logging.getLogger("roblox_app")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Import after logging setup
from .config import BASE_DIR

# Setup paths - use BASE_DIR from config
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Debug information
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Static directory: {STATIC_DIR}")
logger.info(f"Directory contents: {os.listdir(BASE_DIR)}")

# Create FastAPI app
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after FastAPI initialization
from .routers import router
from .dashboard_router import router as dashboard_router

# Include routers
app.include_router(router)
app.include_router(dashboard_router)

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Route handlers
@app.get("/")
@app.get("/dashboard")
async def serve_dashboard(request: Request):
    """Serve the dashboard"""
    return templates.TemplateResponse("dashboard_new.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Roblox API server...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Debug the static file serving
logger.info(f"Static files being served from: {STATIC_DIR}")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Add cache control middleware
@app.middleware("http")
async def add_cache_control_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


```

### api/app/config.py

```py
# api/app/config.py

import os
from pathlib import Path

# Base directory is the api folder
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Games directory is one level up from api folder
GAMES_DIR = BASE_DIR.parent / "games"

# Database paths
DB_DIR = BASE_DIR / "db"
SQLITE_DB_PATH = DB_DIR / "game_data.db"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)

# Storage structure
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = STORAGE_DIR / "assets"  # For RBXMX files
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"  # For asset thumbnails from Roblox CDN
AVATARS_DIR = STORAGE_DIR / "avatars"  # For player avatar images

# Ensure all directories exist
for directory in [STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Replace hard-coded ROBLOX_DIR with dynamic game-specific paths
def get_game_paths(game_slug: str) -> dict:
    """Get game-specific paths"""
    game_dir = GAMES_DIR / game_slug  # Use GAMES_DIR constant
    return {
        'root': game_dir,
        'src': game_dir / "src",
        'assets': game_dir / "src" / "assets",
        'data': game_dir / "src" / "data"
    }

def ensure_game_directories(game_slug: str) -> None:
    """Ensure all required directories exist for a specific game"""
    paths = get_game_paths(game_slug)
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

# API URLs
ROBLOX_API_BASE = "https://thumbnails.roblox.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# NPC Configuration
NPC_SYSTEM_PROMPT_ADDITION = """
When responding, always use the appropriate action type:
- Use "follow" when you intend to start following the player.
- Use "unfollow" when you intend to stop following the player.
- Use "stop_talking" when you want to end the conversation.
- Use "none" for any other response that doesn't require a specific action.

Your response must always include an action, even if it's "none".
"""

```

### api/app/database.py

```py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import json
from .config import SQLITE_DB_PATH
from .paths import get_database_paths

@contextmanager
def get_db():
    db = sqlite3.connect(SQLITE_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def generate_lua_from_db(game_slug: str, db_type: str) -> None:
    """Generate Lua file directly from database data"""
    with get_db() as db:
        db.row_factory = sqlite3.Row
        
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        if db_type == 'asset':
            # Get assets from database
            cursor = db.execute("""
                SELECT asset_id, name, description, type, tags, image_url
                FROM assets WHERE game_id = ?
            """, (game_id,))
            assets = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(db_paths['asset']['lua'], {
                "assets": [{
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset.get("description", ""),
                    "type": asset.get("type", "unknown"),
                    "imageUrl": asset.get("image_url", ""),
                    "tags": json.loads(asset.get("tags", "[]"))
                } for asset in assets]
            })
            
        elif db_type == 'npc':
            # Get NPCs from database
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, model, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs WHERE game_id = ?
            """, (game_id,))
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(db_paths['npc']['lua'], {
                "npcs": [{
                    "id": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "model": npc.get("model", ""),
                    "system_prompt": npc.get("system_prompt", ""),
                    "responseRadius": npc.get("response_radius", 20),
                    "spawnPosition": json.loads(npc.get("spawn_position", "{}")),
                    "abilities": json.loads(npc.get("abilities", "[]")),
                    "shortTermMemory": []
                } for npc in npcs]
            })

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db() as db:
        # Create tables if they don't exist
        db.executescript("""
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
                asset_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                type TEXT,
                tags TEXT,  -- JSON array
                game_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                UNIQUE(asset_id, game_id)
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
        """)
        
        # Ensure game1 exists
        db.execute("""
            INSERT OR IGNORE INTO games (title, slug, description)
            VALUES ('Game 1', 'game1', 'The default game instance')
            ON CONFLICT(slug) DO UPDATE SET
            title = 'Game 1',
            description = 'The default game instance'
        """)
        
        db.commit()

def import_json_to_db(game_slug: str, json_dir: Path) -> None:
    """Import JSON data into database"""
    with get_db() as db:
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        game_id = game['id']
        
        # Import assets
        asset_file = json_dir / 'AssetDatabase.json'
        if asset_file.exists():
            with open(asset_file, 'r') as f:
                asset_data = json.load(f)
                for asset in asset_data.get('assets', []):
                    db.execute("""
                        INSERT OR REPLACE INTO assets 
                        (asset_id, name, description, type, tags, image_url, game_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        asset['assetId'],
                        asset['name'],
                        asset.get('description', ''),
                        asset.get('type', 'unknown'),
                        json.dumps(asset.get('tags', [])),
                        asset.get('imageUrl', ''),
                        game_id
                    ))
        
        # Import NPCs
        npc_file = json_dir / 'NPCDatabase.json'
        if npc_file.exists():
            with open(npc_file, 'r') as f:
                npc_data = json.load(f)
                for npc in npc_data.get('npcs', []):
                    db.execute("""
                        INSERT OR REPLACE INTO npcs 
                        (npc_id, display_name, asset_id, model, system_prompt,
                         response_radius, spawn_position, abilities, game_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        npc['id'],
                        npc['displayName'],
                        npc['assetId'],
                        npc.get('model', ''),
                        npc.get('system_prompt', ''),
                        npc.get('responseRadius', 20),
                        json.dumps(npc.get('spawnPosition', {})),
                        json.dumps(npc.get('abilities', [])),
                        game_id
                    ))
        
        db.commit()

def check_db_state():
    """Check database tables and their contents"""
    with get_db() as db:
        print("\n=== Database State ===")
        
        # Check tables
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name;
        """)
        tables = cursor.fetchall()
        print("Tables:", [table[0] for table in tables])
        
        # Check games
        cursor = db.execute("SELECT * FROM games")
        games = cursor.fetchall()
        print("\nGames in database:")
        for game in games:
            print(f"- {game['title']} (ID: {game['id']}, slug: {game['slug']})")
            
            # Count assets and NPCs for this game
            assets = db.execute("""
                SELECT COUNT(*) as count FROM assets WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            npcs = db.execute("""
                SELECT COUNT(*) as count FROM npcs WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            print(f"  Assets: {assets}")
            print(f"  NPCs: {npcs}")
            
            # Show asset details
            print("\n  Assets:")
            cursor = db.execute("SELECT * FROM assets WHERE game_id = ?", (game['id'],))
            for asset in cursor.fetchall():
                print(f"    - {asset['name']} (ID: {asset['asset_id']})")
            
            # Show NPC details
            print("\n  NPCs:")
            cursor = db.execute("SELECT * FROM npcs WHERE game_id = ?", (game['id'],))
            for npc in cursor.fetchall():
                print(f"    - {npc['display_name']} (ID: {npc['npc_id']})")
        
        print("=====================\n")

def migrate_existing_data():
    """Migrate existing JSON data to SQLite if needed"""
    with get_db() as db:
        # Get the default game
        cursor = db.execute("SELECT id FROM games WHERE slug = 'game1'")
        game = cursor.fetchone()
        if not game:
            print("Error: Default game not found")
            return
            
        default_game_id = game['id']
        
        # Load existing JSON data from the correct paths
        db_paths = get_database_paths("game1")
        
        try:
            # Load JSON data
            with open(db_paths['asset']['json'], 'r') as f:
                asset_data = json.load(f)
            with open(db_paths['npc']['json'], 'r') as f:
                npc_data = json.load(f)
            
            print(f"Found {len(asset_data.get('assets', []))} assets and {len(npc_data.get('npcs', []))} NPCs to migrate")
            
            # Migrate assets
            for asset in asset_data.get('assets', []):
                db.execute("""
                    INSERT OR REPLACE INTO assets 
                    (asset_id, name, description, type, tags, image_url, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset['assetId'],
                    asset['name'],
                    asset.get('description', ''),
                    asset.get('type', 'unknown'),
                    json.dumps(asset.get('tags', [])),
                    asset.get('imageUrl', ''),
                    default_game_id
                ))
            
            # Migrate NPCs
            for npc in npc_data.get('npcs', []):
                db.execute("""
                    INSERT OR REPLACE INTO npcs 
                    (npc_id, display_name, asset_id, model, system_prompt,
                     response_radius, spawn_position, abilities, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    npc['id'],
                    npc['displayName'],
                    npc['assetId'],
                    npc.get('model', ''),
                    npc.get('system_prompt', ''),
                    npc.get('responseRadius', 20),
                    json.dumps(npc.get('spawnPosition', {})),
                    json.dumps(npc.get('abilities', [])),
                    default_game_id
                ))
            
            db.commit()
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.rollback()
            raise

def fetch_all_games():
    """Fetch all games from the database"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            ORDER BY title
        """)
        return [dict(row) for row in cursor.fetchall()]

def create_game(title: str, slug: str, description: str):
    """Create a new game entry"""
    with get_db() as db:
        try:
            cursor = db.execute("""
                INSERT INTO games (title, slug, description)
                VALUES (?, ?, ?)
                RETURNING id
            """, (title, slug, description))
            result = cursor.fetchone()
            db.commit()
            return result['id']
        except Exception as e:
            db.rollback()
            raise e

def fetch_game(slug: str):
    """Fetch a single game by slug"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            WHERE slug = ?
        """, (slug,))
        result = cursor.fetchone()
        return dict(result) if result else None

def update_game(slug: str, title: str, description: str):
    """Update a game's details"""
    with get_db() as db:
        try:
            db.execute("""
                UPDATE games 
                SET title = ?, description = ?
                WHERE slug = ?
            """, (title, description, slug))
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

def delete_game(slug: str):
    """Delete a game and its associated assets and NPCs"""
    with get_db() as db:
        try:
            # Get game ID first
            cursor = db.execute("SELECT id FROM games WHERE slug = ?", (slug,))
            game = cursor.fetchone()
            if not game:
                raise ValueError("Game not found")
                
            game_id = game['id']
            
            # Delete associated NPCs first (due to foreign key constraints)
            db.execute("DELETE FROM npcs WHERE game_id = ?", (game_id,))
            
            # Delete associated assets
            db.execute("DELETE FROM assets WHERE game_id = ?", (game_id,))
            
            # Finally delete the game
            db.execute("DELETE FROM games WHERE id = ?", (game_id,))
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

def count_assets(game_id: int):
    """Count assets for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM assets 
            WHERE game_id = ?
        """, (game_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0

def count_npcs(game_id: int):
    """Count NPCs for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM npcs 
            WHERE game_id = ?
        """, (game_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0

def fetch_assets_by_game(game_id: int):
    """Fetch assets for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM assets 
            WHERE game_id = ?
            ORDER BY name
        """, (game_id,))
        return [dict(row) for row in cursor.fetchall()]

def fetch_npcs_by_game(game_id: int):
    """Fetch NPCs for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT n.*, a.image_url
            FROM npcs n
            JOIN assets a ON n.asset_id = a.asset_id
            WHERE n.game_id = ?
            ORDER BY n.display_name
        """, (game_id,))
        return [dict(row) for row in cursor.fetchall()]

```

### api/app/db.py

```py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger("roblox_app")

# Get database path from config
from .config import SQLITE_DB_PATH

@contextmanager
def get_db():
    """Get a database connection with context management"""
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {SQLITE_DB_PATH}")
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed") 
```

### api/app/utils.py

```py
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional
from .config import get_game_paths, BASE_DIR, GAMES_DIR
from .db import get_db
import os
import shutil
import logging
from .paths import get_database_paths

# Set up logger
logger = logging.getLogger("roblox_app")

def load_json_database(path: Path) -> dict:
    """Load a JSON database file"""
    try:
        if not path.exists():
            return {"assets": [], "npcs": []}
            
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON database from {path}: {e}")
        return {"assets": [], "npcs": []}

def save_json_database(path: Path, data: dict) -> None:
    """Save data to a JSON database file"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON database to {path}: {e}")
        raise

def format_npc_as_lua(npc: dict, db=None) -> str:
    """Format a single NPC as Lua code"""
    try:
        # Handle abilities - could be string or list
        abilities_raw = npc.get('abilities', '[]')
        if isinstance(abilities_raw, list):
            abilities = abilities_raw  # Already a list
        else:
            abilities = json.loads(abilities_raw)  # Parse JSON string
            
        # Format abilities as Lua table with proper indentation
        abilities_lua = "{\n" + "".join(f'            "{ability}", \n' for ability in abilities) + "        }"
            
        # Use new coordinate columns directly
        vector3 = f"Vector3.new({npc['spawn_x']}, {npc['spawn_y']}, {npc['spawn_z']})"

        # Use the assetId as the model name
        model = npc['asset_id']
        display_name = npc['display_name']
            
        return (f"        {{\n"
                f"            id = \"{npc['npc_id']}\", \n"
                f"            displayName = \"{display_name}\", \n"
                f"            name = \"{display_name}\", \n"
                f"            assetId = \"{model}\", \n"
                f"            model = \"{model}\", \n"
                f"            modelName = \"{display_name}\", \n"
                f"            system_prompt = \"{npc.get('system_prompt', '')}\", \n"
                f"            responseRadius = {npc.get('response_radius', 20)}, \n"
                f"            spawnPosition = {vector3}, \n"
                f"            abilities = {abilities_lua}, \n"
                f"            shortTermMemory = {{}}, \n"
                f"        }},")
    except Exception as e:
        logger.error(f"Error formatting NPC as Lua: {e}")
        logger.error(f"NPC data: {npc}")
        raise

def format_asset_as_lua(asset: dict) -> str:
    """Format single asset as Lua table entry"""
    # Escape any quotes in the description
    description = asset['description'].replace('"', '\\"')
    
    # Match the NPC style formatting
    return (f"        {{\n"
            f"            assetId = \"{asset['asset_id']}\",\n"
            f"            name = \"{asset['name']}\",\n"
            f"            description = \"{description}\",\n"
            f"        }},\n")

def save_lua_database(game_slug: str, db: sqlite3.Connection) -> None:
    """Save both NPC and Asset Lua databases for a game"""
    try:
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
            
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        # Generate Asset Database
        cursor = db.execute("""
            SELECT asset_id, name, description
            FROM assets 
            WHERE game_id = ?
            ORDER BY name
        """, (game_id,))
        assets = cursor.fetchall()
        
        # Format and save assets
        asset_lua = "return {\n    assets = {\n"
        for asset in assets:
            formatted = format_asset_as_lua(dict(asset))
            asset_lua += formatted
        asset_lua += "    },\n}"
        
        with open(db_paths['asset']['lua'], 'w', encoding='utf-8') as f:
            f.write(asset_lua)
            logger.info(f"Wrote asset database to {db_paths['asset']['lua']}")

        # Generate NPC Database - Include new coordinate columns
        cursor = db.execute("""
            SELECT 
                npc_id,
                display_name,
                asset_id,
                system_prompt,
                response_radius,
                spawn_x,
                spawn_y,
                spawn_z,
                abilities
            FROM npcs 
            WHERE game_id = ?
            ORDER BY display_name
        """, (game_id,))
        npcs = cursor.fetchall()
        
        # Format and save NPCs
        npc_lua = "return {\n    npcs = {\n"
        for npc in npcs:
            npc_lua += format_npc_as_lua(dict(npc))
        npc_lua += "\n    },\n}"
        
        with open(db_paths['npc']['lua'], 'w', encoding='utf-8') as f:
            f.write(npc_lua)
            logger.info(f"Wrote NPC database to {db_paths['npc']['lua']}")
            
    except Exception as e:
        logger.error(f"Error saving Lua databases: {str(e)}")
        raise

def generate_lua_from_db(game_slug: str, db_type: str) -> None:
    """Generate Lua file directly from database data"""
    with get_db() as db:
        db.row_factory = sqlite3.Row
        
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        if db_type == 'asset':
            # Get assets from database
            cursor = db.execute("""
                SELECT asset_id, name, description, type, tags, image_url
                FROM assets WHERE game_id = ?
            """, (game_id,))
            assets = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(game_slug, db)
            
        elif db_type == 'npc':
            # Get NPCs from database
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, model, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs WHERE game_id = ?
            """, (game_id,))
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file - pass db connection
            save_lua_database(game_slug, db)

def sync_game_files(game_slug: str) -> None:
    """Sync both JSON and Lua files from database"""
    generate_lua_from_db(game_slug, 'asset')
    generate_lua_from_db(game_slug, 'npc')

def ensure_game_directories(game_slug: str) -> Dict[str, Path]:
    """Create and return game directory structure"""
    print("Starting ensure_game_directories")
    try:
        logger.info(f"Games directory: {GAMES_DIR}")
        logger.info(f"Games directory exists: {GAMES_DIR.exists()}")
        
        # Create GAMES_DIR if it doesn't exist
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Created or verified GAMES_DIR exists")
        
        game_root = GAMES_DIR / game_slug
        logger.info(f"Game root will be: {game_root}")
        
        # Copy from template location
        template_dir = GAMES_DIR / "_template"
        logger.info(f"Looking for template at: {template_dir}")
        logger.info(f"Template directory exists: {template_dir.exists()}")
        
        if not template_dir.exists():
            logger.error(f"Template directory not found at: {template_dir}")
            raise FileNotFoundError(f"Template not found at {template_dir}")
            
        logger.info(f"Using template from: {template_dir}")
        
        if game_root.exists():
            logger.info(f"Removing existing game directory: {game_root}")
            shutil.rmtree(game_root)
            
        logger.info(f"Copying template to: {game_root}")
        # Use copytree with ignore_dangling_symlinks=True and dirs_exist_ok=True
        shutil.copytree(template_dir, game_root, symlinks=False, 
                       ignore_dangling_symlinks=True, 
                       dirs_exist_ok=True)
        
        # Define and ensure all required paths exist
        paths = {
            'root': game_root,
            'src': game_root / "src",
            'data': game_root / "src" / "data",
            'assets': game_root / "src" / "assets",
            'npcs': game_root / "src" / "assets" / "npcs"
        }
        
        # Create directories if they don't exist
        for path_name, path in paths.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created {path_name} directory at: {path}")
            
        logger.info(f"Successfully created game directories for {game_slug}")
        logger.info(f"Returning paths dictionary: {paths}")
        return paths
        
    except Exception as e:
        logger.error(f"Error in ensure_game_directories: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        raise

```

### api/app/paths.py

```py
from pathlib import Path
from typing import Dict
from .config import get_game_paths

def get_database_paths(game_slug: str = "game1") -> Dict[str, Dict[str, Path]]:
    """
    Get paths to database files for a specific game
    
    Args:
        game_slug (str): The game identifier (e.g., "game1", "game2")
        
    Returns:
        Dict containing paths to JSON and Lua database files
    """
    game_paths = get_game_paths(game_slug)
    data_dir = game_paths['data']
    
    # Ensure the data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'asset': {
            'json': data_dir / 'AssetDatabase.json',
            'lua': data_dir / 'AssetDatabase.lua'
        },
        'npc': {
            'json': data_dir / 'NPCDatabase.json',
            'lua': data_dir / 'NPCDatabase.lua'
        }
    } 
```

### api/app/storage.py

```py
# api/app/storage.py

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from fastapi import UploadFile
import xml.etree.ElementTree as ET
import requests
from io import BytesIO
from PIL import Image
from .config import STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR

logger = logging.getLogger("file_manager")

class FileStorageManager:
    def __init__(self, game_slug=None):
        self.game_slug = game_slug
        self.storage_dir = STORAGE_DIR / (game_slug if game_slug else "default")
        self.assets_dir = self.storage_dir / "assets"
        self.thumbnails_dir = self.storage_dir / "thumbnails"
        self.avatars_dir = self.storage_dir / "avatars"
        
        # Ensure directories exist
        for directory in [self.storage_dir, self.assets_dir, 
                         self.thumbnails_dir, self.avatars_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def store_asset_file(self, file: UploadFile, asset_type: str) -> dict:
        """Store an asset file in the appropriate Roblox assets subdirectory."""
        try:
            # Get original filename and standardize it
            original_name = os.path.splitext(file.filename)[0].lower()
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            # Standardize filename
            safe_filename = ''.join(c if c.isalnum() or c == '_' else '_' 
                                  for c in original_name.replace(' ', '_'))
            
            if file_ext not in ['.rbxm', '.rbxmx']:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Create type directory if it doesn't exist
            type_dir = self.assets_dir / asset_type.lower()
            type_dir.mkdir(exist_ok=True)
            
            # Store in appropriate directory
            file_path = type_dir / f"{safe_filename}{file_ext}"
            
            logger.info(f"Attempting to save file to: {file_path}")
            
            # Save the file
            with open(file_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"Successfully stored asset file at: {file_path}")
            
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "size": file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Error storing asset file: {e}")
            raise

    async def store_avatar_image(self, user_id: str, url: str) -> str:
        """Store a player's avatar image."""
        save_path = self.avatars_dir / f"{user_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def store_asset_thumbnail(self, asset_id: str, url: str) -> str:
        """Store an asset's thumbnail image."""
        save_path = self.thumbnails_dir / f"{asset_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def download_and_store_image(self, url: str, save_path: Path) -> str:
        """Download an image from URL and store it locally."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image.save(save_path)
            return str(save_path)
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            raise

    def get_avatar_path(self, user_id: str) -> Optional[Path]:
        """Get path to stored avatar image."""
        path = self.avatars_dir / f"{user_id}.png"
        return path if path.exists() else None

    def get_thumbnail_path(self, asset_id: str) -> Optional[Path]:
        """Get path to stored thumbnail image."""
        path = self.thumbnails_dir / f"{asset_id}.png"
        return path if path.exists() else None

    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get path to stored asset file."""
        for ext in ['.rbxmx', '.rbxm']:
            path = self.assets_dir / f"{asset_id}{ext}"
            if path.exists():
                return path
        return None

    async def cleanup(self) -> Tuple[int, int, int]:
        """Clean up unused files and return count of deleted files."""
        # Implementation of cleanup logic
        pass

    async def delete_asset_files(self, asset_id: str) -> None:
        """Delete all files associated with an asset."""
        try:
            # Delete thumbnail
            thumbnail_path = self.thumbnails_dir / f"{asset_id}.png"
            if thumbnail_path.exists():
                thumbnail_path.unlink()

            # Delete asset file (try both .rbxmx and .rbxm extensions)
            for ext in ['.rbxmx', '.rbxm']:
                asset_path = self.assets_dir / f"{asset_id}{ext}"
                if asset_path.exists():
                    asset_path.unlink()

            logger.info(f"Successfully deleted files for asset {asset_id}")
        except Exception as e:
            logger.error(f"Error deleting asset files: {e}")
            raise

```

### api/app/image_utils.py

```py
# api/app/image_utils.py

import requests
import logging
from PIL import Image
from io import BytesIO
from fastapi import HTTPException
from typing import Tuple
from pathlib import Path
from .config import AVATARS_DIR, THUMBNAILS_DIR
from openai import OpenAI, OpenAIError
import base64
import os

logger = logging.getLogger("image_utils")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def download_image(url: str, save_path: Path) -> str:
    """Generic image download function."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(save_path)
        return str(save_path)
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download image.")

async def download_avatar_image(user_id: str) -> str:
    """Download and save player avatar image."""
    avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
    try:
        response = requests.get(avatar_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        save_path = AVATARS_DIR / f"{user_id}.png"
        return download_image(image_url, save_path)
    except Exception as e:
        logger.error(f"Error fetching avatar image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download avatar image.")

async def download_asset_image(asset_id: str) -> Tuple[str, str]:
    """Download and save asset thumbnail."""
    asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
    try:
        response = requests.get(asset_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        save_path = THUMBNAILS_DIR / f"{asset_id}.png"
        local_path = download_image(image_url, save_path)
        return local_path, image_url
    except Exception as e:
        logger.error(f"Error fetching asset image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download asset image.")

async def generate_image_description(
    image_path: str, 
    prompt: str, 
    max_length: int = 300
) -> str:
    """Generate AI description for an image."""
    base64_image = encode_image(image_path)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt} Limit the description to {max_length} characters."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        }
                    ],
                }
            ]
        )
        description = response.choices[0].message.content
        return description
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "No description available."

async def get_asset_description(asset_id: str, name: str) -> dict:
    """Get asset description and image URL."""
    try:
        image_path, image_url = await download_asset_image(asset_id)
        prompt = (
            "Please provide a detailed description of this Roblox asset image. "
            "Include details about its appearance, features, and any notable characteristics."
        )
        ai_description = await generate_image_description(image_path, prompt)
        return {
            "description": ai_description,
            "imageUrl": image_url
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing asset description request: {e}")
        return {"error": f"Failed to process request: {str(e)}"}
```

### api/app/__init__.py

```py

```

### api/app/routers.py

```py
import os
import logging
import json
from typing import Literal, Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI, OpenAIError
from app.conversation_manager import ConversationManager
from app.config import (
    NPC_SYSTEM_PROMPT_ADDITION,
    STORAGE_DIR, 
    ASSETS_DIR, 
    THUMBNAILS_DIR, 
    AVATARS_DIR
)
from .utils import (
    load_json_database, 
    save_json_database, 
    save_lua_database, 
    get_database_paths
)
from .image_utils import (
    download_avatar_image,
    download_asset_image,
    generate_image_description,
    get_asset_description
)
from .database import get_db
from .storage import FileStorageManager

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get database paths
DB_PATHS = get_database_paths()

# Initialize logging and router
logger = logging.getLogger("ella_app")
router = APIRouter()

# Pydantic Models
class PerceptionData(BaseModel):
    visible_objects: List[str] = Field(default_factory=list)
    visible_players: List[str] = Field(default_factory=list)
    memory: List[Dict[str, Any]] = Field(default_factory=list)

class EnhancedChatMessageV3(BaseModel):
    message: str
    player_id: str
    npc_id: str
    npc_name: str
    system_prompt: str
    perception: Optional[PerceptionData] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limit: int = 200

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "stop_talking", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: NPCAction
    internal_state: Optional[Dict[str, Any]] = None

class PlayerDescriptionRequest(BaseModel):
    user_id: str

class PlayerDescriptionResponse(BaseModel):
    description: str

class AssetData(BaseModel):
    asset_id: str
    name: str

class AssetResponse(BaseModel):
    asset_id: str
    name: str
    description: str
    image_url: str

class UpdateAssetsRequest(BaseModel):
    overwrite: bool = False
    single_asset: Optional[str] = None
    only_empty: bool = False

class EditItemRequest(BaseModel):
    id: str
    description: str

# Initialize conversation manager
conversation_manager = ConversationManager()


# def generate_avatar_description_from_image(image_path: str, max_length: int = 300) -> str:
#     base64_image = encode_image(image_path)
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": (
#                                 f"Please provide a detailed description of this Roblox avatar within {max_length} characters. "
#                                 "Include details about the avatar's clothing, accessories, colors, any unique features, and its overall style or theme."
#                             ),
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_image}"
#                             },
#                         }
#                     ],
#                 }
#             ]
#         )
#         description = response.choices[0].message.content
#         return description
#     except OpenAIError as e:
#         logger.error(f"OpenAI API error: {e}")
#         return "No description available."

# def download_avatar_image(user_id: str) -> str:
#     avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
#     try:
#         response = requests.get(avatar_api_url)
#         response.raise_for_status()
#         image_url = response.json()['data'][0]['imageUrl']
#         return download_image(image_url, os.path.join(AVATAR_SAVE_PATH, f"{user_id}.png"))
#     except Exception as e:
#         logger.error(f"Error fetching avatar image: {e}")
#         raise HTTPException(status_code=500, detail="Failed to download avatar image.")

# def download_asset_image(asset_id: str) -> tuple[str, str]:
#     asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
#     try:
#         response = requests.get(asset_api_url)
#         response.raise_for_status()
#         image_url = response.json()['data'][0]['imageUrl']
#         local_path = os.path.join(ASSET_IMAGE_SAVE_PATH, f"{asset_id}.png")
#         download_image(image_url, local_path)
#         return local_path, image_url
#     except Exception as e:
#         logger.error(f"Error fetching asset image: {e}")
#         raise HTTPException(status_code=500, detail="Failed to download asset image.")

# def generate_description_from_image(image_path: str, prompt: str, max_length: int = 300) -> str:
#     base64_image = encode_image(image_path)
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": f"{prompt} Limit the description to {max_length} characters."
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_image}"
#                             },
#                         }
#                     ],
#                 }
#             ]
#         )
#         description = response.choices[0].message.content
#         return description
#     except OpenAIError as e:
#         logger.error(f"OpenAI API error: {e}")
#         return "No description available."

# @router.post("/get_asset_description")
# async def get_asset_description(data: AssetData):
#     try:
#         image_path, image_url = download_asset_image(data.asset_id)
#         prompt = (
#             "Please provide a detailed description of this Roblox asset image. "
#             "Include details about its appearance, features, and any notable characteristics."
#         )
#         ai_description = generate_description_from_image(image_path, prompt)
#         return {
#             "description": ai_description,
#             "imageUrl": image_url
#         }
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error processing asset description request: {e}")
#         return {"error": f"Failed to process request: {str(e)}"}

# @router.post("/get_player_description")
# async def get_player_description(data: PlayerDescriptionRequest):
#     try:
#         image_path = download_avatar_image(data.user_id)
#         ai_description = generate_avatar_description_from_image(image_path)
#         return {"description": ai_description}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error processing player description request: {e}")
#         return {"error": f"Failed to process request: {str(e)}"}


@router.post("/get_asset_description")
async def get_asset_description_endpoint(data: AssetData):
    """Endpoint to get asset description using AI."""
    try:
        result = await get_asset_description(data.asset_id, data.name)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing asset description request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get_player_description")
async def get_player_description_endpoint(data: PlayerDescriptionRequest):
    """Endpoint to get player avatar description using AI."""
    try:
        # Download image and get its path
        image_path = await download_avatar_image(data.user_id)
        
        # Generate description using the generic description function
        prompt = (
            "Please provide a detailed description of this Roblox avatar. "
            "Include details about the avatar's clothing, accessories, colors, "
            "unique features, and overall style or theme."
        )
        description = await generate_image_description(image_path, prompt)
        
        return {"description": description}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing player description request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/robloxgpt/v3")
async def enhanced_chatgpt_endpoint_v3(request: Request):
    logger.info(f"Received request to /robloxgpt/v3 endpoint")

    try:
        data = await request.json()
        logger.debug(f"Request data: {data}")

        chat_message = EnhancedChatMessageV3(**data)
        logger.info(f"Validated enhanced chat message: {chat_message}")
    except Exception as e:
        logger.error(f"Failed to parse or validate data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    # Fetch the OpenAI API key from the environment
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found")
        raise HTTPException(status_code=500, detail="OpenAI API key not found")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    conversation = conversation_manager.get_conversation(chat_message.player_id, chat_message.npc_id)
    logger.debug(f"Conversation history: {conversation}")

    try:
        context_summary = f"""
        NPC: {chat_message.npc_name}. 
        Player: {chat_message.context.get('player_name', 'Unknown')}. 
        New conversation: {chat_message.context.get('is_new_conversation', True)}. 
        Time since last interaction: {chat_message.context.get('time_since_last_interaction', 'N/A')}. 
        Nearby players: {', '.join(chat_message.context.get('nearby_players', []))}. 
        NPC location: {chat_message.context.get('npc_location', 'Unknown')}.
        """

        if chat_message.perception:
            context_summary += f"""
            Visible objects: {', '.join(chat_message.perception.visible_objects)}.
            Visible players: {', '.join(chat_message.perception.visible_players)}.
            Recent memories: {', '.join([str(m) for m in chat_message.perception.memory[-5:]])}.
            """

        logger.debug(f"Context summary: {context_summary}")

        system_prompt = f"{chat_message.system_prompt}\n\n{NPC_SYSTEM_PROMPT_ADDITION}\n\nContext: {context_summary}"

        messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": "assistant" if i % 2 else "user", "content": msg} for i, msg in enumerate(conversation)],
            {"role": "user", "content": chat_message.message}
        ]
        logger.debug(f"Messages to OpenAI: {messages}")

        logger.info(f"Sending request to OpenAI API for NPC: {chat_message.npc_name}")
        try:
            # Using beta.chat.completions.parse for structured output
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=chat_message.limit,
                response_format=NPCResponseV3
            )

            # Check if the model refused the request
            if response.choices[0].finish_reason == "refusal":
                logger.error(f"Model refused to comply: {response.choices[0].message.content}")
                npc_response = NPCResponseV3(
                    message="I'm sorry, but I can't assist with that request.",
                    action=NPCAction(type="none")
                )
            else:
                # Parse the response content
                ai_message = response.choices[0].message.content
                npc_response = NPCResponseV3(**json.loads(ai_message))
                logger.debug(f"Parsed NPC response: {npc_response}")
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            npc_response = NPCResponseV3(
                message="I'm sorry, I'm having trouble understanding right now.",
                action=NPCAction(type="none")
            )
        except Exception as e:
            logger.error(f"Error processing OpenAI API request: {e}", exc_info=True)
            npc_response = NPCResponseV3(
                message="I'm sorry, I'm having trouble understanding right now.",
                action=NPCAction(type="none")
            )

        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, chat_message.message)
        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, npc_response.message)

        return JSONResponse(npc_response.dict())

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.post("/robloxgpt/v3/heartbeat")
async def heartbeat_update(request: Request):
    try:
        data = await request.json()
        npc_id = data.get("npc_id")
        logs = data.get("logs", [])
        logger.info(f"Heartbeat received from NPC: {npc_id}")
        logger.debug(f"Logs received: {logs}")

        return JSONResponse({"status": "acknowledged"})
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=400, detail=str(e))


```

### api/app/dashboard_router.py

```py
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
import shutil
import os
from slugify import slugify as python_slugify
from .utils import (
    load_json_database, 
    save_json_database, 
    save_lua_database, 
    get_database_paths,
    ensure_game_directories
)
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import (
    STORAGE_DIR, 
    ASSETS_DIR, 
    THUMBNAILS_DIR, 
    AVATARS_DIR,
    get_game_paths,
    BASE_DIR
)
from .database import (
    get_db,
    fetch_all_games,
    create_game,
    fetch_game,
    update_game,
    delete_game,
    count_assets,
    count_npcs,
    fetch_assets_by_game,
    fetch_npcs_by_game
)
import uuid
from fastapi.templating import Jinja2Templates
import sqlite3

logger = logging.getLogger("roblox_app")
router = APIRouter()

# Set up templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def slugify(text):
    """Generate a unique slug for the game."""
    base_slug = python_slugify(text, separator='-', lowercase=True)
    slug = base_slug
    counter = 1
    
    with get_db() as db:
        while True:
            # Check if slug exists
            cursor = db.execute("SELECT 1 FROM games WHERE slug = ?", (slug,))
            if not cursor.fetchone():
                break
            # If exists, append counter and try again
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    logger.info(f"Generated unique slug: {slug} from title: {text}")
    return slug

@router.get("/api/games")
async def list_games():
    try:
        logger.info("Fetching games list")
        games = fetch_all_games()  # Using non-async version
        logger.info(f"Found {len(games)} games")
        
        formatted_games = []
        for game in games:
            game_data = {
                'id': game['id'],
                'title': game['title'],
                'slug': game['slug'],
                'description': game['description'],
                'asset_count': count_assets(game['id']),
                'npc_count': count_npcs(game['id'])
            }
            formatted_games.append(game_data)
            logger.info(f"Game: {game_data['title']} (ID: {game_data['id']}, Assets: {game_data['asset_count']}, NPCs: {game_data['npc_count']})")
        
        return JSONResponse(formatted_games)
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return JSONResponse({"error": "Failed to fetch games"}, status_code=500)

@router.get("/api/games/{slug}")
async def get_game(slug: str):
    try:
        game = fetch_game(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return JSONResponse(game)
    except Exception as e:
        logger.error(f"Error fetching game: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/games")
async def create_game_endpoint(request: Request):
    try:
        data = await request.json()
        game_slug = slugify(data['title'])
        clone_from = data.get('cloneFrom')  # Get the source game slug if cloning
        
        logger.info(f"Creating game with title: {data['title']}, slug: {game_slug}, clone from: {clone_from}")
        
        try:
            # Create game directories from template
            logger.info("About to call ensure_game_directories")
            paths = ensure_game_directories(game_slug)
            logger.info(f"Got paths back: {paths}")
            
            if not paths:
                logger.error("ensure_game_directories returned None")
                raise ValueError("Failed to create game directories - no paths returned")
                
            logger.info(f"Created game directories at: {paths['root']}")
            
            with get_db() as db:
                try:
                    # Start transaction
                    db.execute('BEGIN')
                    
                    # Create game in database
                    game_id = create_game(data['title'], game_slug, data['description'])
                    logger.info(f"Created game in database with ID: {game_id}")
                    
                    # If cloning from another game
                    if clone_from:
                        logger.info(f"Cloning data from game: {clone_from}")
                        
                        # Get source game ID
                        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (clone_from,))
                        source_game = cursor.fetchone()
                        if not source_game:
                            raise ValueError(f"Source game {clone_from} not found")
                        
                        source_game_id = source_game['id']
                        
                        # Clone assets
                        logger.info("Cloning assets...")
                        db.execute("""
                            INSERT INTO assets (
                                game_id, asset_id, name, description, image_url, type, tags
                            )
                            SELECT 
                                ?, asset_id, name, description, image_url, type, tags
                            FROM assets 
                            WHERE game_id = ?
                        """, (game_id, source_game_id))
                        
                        # Clone NPCs with new IDs
                        logger.info("Cloning NPCs...")
                        cursor = db.execute("""
                            SELECT 
                                display_name, asset_id, model,
                                system_prompt, response_radius, spawn_x, spawn_y, spawn_z,
                                abilities
                            FROM npcs 
                            WHERE game_id = ?
                        """, (source_game_id,))
                        
                        npcs = cursor.fetchall()
                        for npc in npcs:
                            new_npc_id = str(uuid.uuid4())  # Generate new unique ID
                            db.execute("""
                                INSERT INTO npcs (
                                    game_id, npc_id, display_name, asset_id, model,
                                    system_prompt, response_radius, spawn_x, spawn_y, spawn_z,
                                    abilities
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                game_id,
                                new_npc_id,
                                npc['display_name'],
                                npc['asset_id'],
                                npc['model'],
                                npc['system_prompt'],
                                npc['response_radius'],
                                npc['spawn_x'],
                                npc['spawn_y'],
                                npc['spawn_z'],
                                npc['abilities']
                            ))
                        
                        # Copy asset files
                        source_paths = get_game_paths(clone_from)
                        if source_paths['assets'].exists():
                            shutil.copytree(
                                source_paths['assets'], 
                                paths['assets'],
                                dirs_exist_ok=True
                            )
                            logger.info("Copied asset files")
                    
                    # Update project.json name
                    project_file = paths['root'] / "default.project.json"
                    if project_file.exists():
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                        project_data['name'] = data['title']
                        with open(project_file, 'w') as f:
                            json.dump(project_data, f, indent=2)
                        logger.info("Updated project.json")
                    
                    # Initialize/update Lua databases
                    save_lua_database(game_slug, db)
                    logger.info("Generated Lua databases")
                    
                    db.commit()
                    logger.info("Database transaction committed")
                    
                    return JSONResponse({
                        "id": game_id,
                        "slug": game_slug,
                        "message": "Game created successfully"
                    })
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Database error: {str(e)}")
                    raise
                
        except Exception as e:
            logger.error(f"Failed to create game directories: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.put("/api/games/{slug}")
async def update_game_endpoint(slug: str, request: Request):
    try:
        data = await request.json()
        update_game(slug, data['title'], data['description'])  # Using non-async version
        return JSONResponse({"message": "Game updated successfully"})
    except Exception as e:
        logger.error(f"Error updating game: {str(e)}")
        return JSONResponse({"error": "Failed to update game"}, status_code=500)

@router.delete("/api/games/{slug}")
async def delete_game_endpoint(slug: str):
    try:
        logger.info(f"Deleting game: {slug}")
        
        with get_db() as db:
            try:
                # Start transaction
                db.execute('BEGIN')
                
                # Get game ID first
                cursor = db.execute("SELECT id FROM games WHERE slug = ?", (slug,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                game_id = game['id']
                
                # Delete NPCs and assets first (foreign key constraints)
                db.execute("DELETE FROM npcs WHERE game_id = ?", (game_id,))
                db.execute("DELETE FROM assets WHERE game_id = ?", (game_id,))
                
                # Delete game
                db.execute("DELETE FROM games WHERE id = ?", (game_id,))
                
                # Delete game directory
                game_dir = Path(os.path.dirname(BASE_DIR)) / "games" / slug
                if game_dir.exists():
                    shutil.rmtree(game_dir)
                    logger.info(f"Deleted game directory: {game_dir}")
                
                db.commit()
                logger.info(f"Successfully deleted game {slug}")
                
                return JSONResponse({"message": "Game deleted successfully"})
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error in transaction, rolling back: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/assets")
async def list_assets(game_id: Optional[int] = None, type: Optional[str] = None):
    try:
        with get_db() as db:
            logger.info(f"Fetching assets for game_id: {game_id}, type: {type}")

            # Build query based on game_id and type
            if game_id and type:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    WHERE a.game_id = ? AND a.type = ?
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """, (game_id, type))
            elif game_id:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    WHERE a.game_id = ?
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count, g.title as game_title
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    LEFT JOIN games g ON a.game_id = g.id
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """)

            assets = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Found {len(assets)} assets")

            # Format the response
            formatted_assets = []
            for asset in assets:
                formatted_assets.append({
                    "id": asset["id"],
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset["description"],
                    "imageUrl": asset["image_url"],
                    "type": asset["type"],
                    "tags": json.loads(asset["tags"]) if asset["tags"] else [],
                    "npcCount": asset["npc_count"],
                    "gameTitle": asset.get("game_title")
                })

            return JSONResponse({"assets": formatted_assets})
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        return JSONResponse({"error": f"Failed to fetch assets: {str(e)}"}, status_code=500)

def get_valid_npcs(db, game_id):
    """Get only valid NPCs (with required fields and valid assets)"""
    cursor = db.execute("""
        SELECT n.*, a.name as asset_name, a.image_url
        FROM npcs n
        JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
        WHERE n.game_id = ?
            AND n.display_name IS NOT NULL 
            AND n.display_name != ''
            AND n.asset_id IS NOT NULL 
            AND n.asset_id != ''
        ORDER BY n.display_name
    """, (game_id,))
    return cursor.fetchall()

@router.get("/api/npcs")
async def list_npcs(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            if game_id:
                cursor = db.execute("""
                    SELECT DISTINCT
                        n.id,
                        n.npc_id,
                        n.display_name,
                        n.asset_id,
                        n.model,
                        n.system_prompt,
                        n.response_radius,
                        n.spawn_x,
                        n.spawn_y,
                        n.spawn_z,
                        n.abilities,
                        a.name as asset_name,
                        a.image_url
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                    WHERE n.game_id = ?
                    ORDER BY n.display_name
                """, (game_id,))
            else:
                # Similar query for all NPCs...
                pass
            
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Format the response with new coordinate structure
            formatted_npcs = []
            for npc in npcs:
                npc_data = {
                    "id": npc["id"],
                    "npcId": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "assetName": npc["asset_name"],
                    "model": npc["model"],
                    "systemPrompt": npc["system_prompt"],
                    "responseRadius": npc["response_radius"],
                    "spawnPosition": {  # Format coordinates for frontend
                        "x": npc["spawn_x"],
                        "y": npc["spawn_y"],
                        "z": npc["spawn_z"]
                    },
                    "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                    "imageUrl": npc["image_url"]
                }
                formatted_npcs.append(npc_data)
            
            return JSONResponse({"npcs": formatted_npcs})
            
    except Exception as e:
        logger.error(f"Error fetching NPCs: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPCs"}, status_code=500)

@router.put("/api/games/{game_id}/assets/{asset_id}")
async def update_asset(game_id: int, asset_id: str, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating asset {asset_id} for game {game_id} with data: {data}")
        
        with get_db() as db:
            try:
                # First get game info
                cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                
                game_slug = game['slug']
                
                # Update asset in database
                cursor.execute("""
                    UPDATE assets 
                    SET name = ?,
                        description = ?
                    WHERE game_id = ? AND asset_id = ?
                    RETURNING *
                """, (
                    data['name'],
                    data['description'],
                    game_id,
                    asset_id
                ))
                
                updated = cursor.fetchone()
                if not updated:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Update Lua files - pass game_slug instead of file path
                save_lua_database(game_slug, db)
                
                db.commit()
                
                # Format response
                asset_data = {
                    "id": updated["id"],
                    "assetId": updated["asset_id"],
                    "name": updated["name"],
                    "description": updated["description"],
                    "type": updated["type"],
                    "imageUrl": updated["image_url"],
                    "tags": json.loads(updated["tags"]) if updated["tags"] else []
                }
                
                return JSONResponse(asset_data)
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error updating asset: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str, game_id: int):
    """Get a single NPC by ID"""
    try:
        logger.info(f"Fetching NPC {npc_id} for game {game_id}")
        
        with get_db() as db:
            # Get NPC with asset info
            cursor = db.execute("""
                SELECT n.*, a.name as asset_name, a.image_url
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            
            npc = cursor.fetchone()
            if not npc:
                logger.error(f"NPC not found: {npc_id}")
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Convert sqlite3.Row to dict
            npc = dict(npc)
            
            # Format response
            npc_data = {
                "id": npc["id"],
                "npcId": npc["npc_id"],
                "displayName": npc["display_name"],
                "assetId": npc["asset_id"],
                "assetName": npc["asset_name"],
                "systemPrompt": npc["system_prompt"],
                "responseRadius": npc["response_radius"],
                "spawnPosition": {
                    "x": npc["spawn_x"],
                    "y": npc["spawn_y"],
                    "z": npc["spawn_z"]
                },
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "imageUrl": npc["image_url"]
            }
            
            logger.info(f"Found NPC: {npc_data}")
            return JSONResponse(npc_data)
            
    except Exception as e:
        logger.error(f"Error fetching NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/npcs/{npc_id}")
async def update_npc(npc_id: str, game_id: int, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating NPC {npc_id} with data: {data}")
        
        with get_db() as db:
            # First get game info for Lua update
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']
            
            # Extract and validate spawn coordinates
            spawn_pos = data.get('spawnPosition', {})
            try:
                spawn_x = float(spawn_pos.get('x', 0))
                spawn_y = float(spawn_pos.get('y', 5))
                spawn_z = float(spawn_pos.get('z', 0))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid spawn coordinates"
                )
            
            # Get cursor from db connection
            cursor = db.cursor()
            
            # Update NPC with new coordinate columns
            cursor.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    system_prompt = ?,
                    response_radius = ?,
                    spawn_x = ?,
                    spawn_y = ?,
                    spawn_z = ?,
                    abilities = ?
                WHERE npc_id = ? AND game_id = ?
            """, (
                data['displayName'],
                data['assetId'],
                data['systemPrompt'],
                data['responseRadius'],
                spawn_x,
                spawn_y,
                spawn_z,
                json.dumps(data['abilities']),
                npc_id,
                game_id
            ))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Fetch updated NPC data
            cursor.execute("""
                SELECT n.*, a.name as asset_name, a.image_url
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            
            updated = cursor.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Updated NPC not found")
            
            # Convert sqlite3.Row to dict before accessing with get()
            updated_dict = dict(updated)
            
            # Format response with new coordinate structure
            npc_data = {
                "id": updated_dict["id"],
                "npcId": updated_dict["npc_id"],
                "displayName": updated_dict["display_name"],
                "assetId": updated_dict["asset_id"],
                "assetName": updated_dict.get("asset_name"),  # Now we can use .get()
                "systemPrompt": updated_dict["system_prompt"],
                "responseRadius": updated_dict["response_radius"],
                "spawnPosition": {  # Format coordinates for frontend
                    "x": updated_dict["spawn_x"],
                    "y": updated_dict["spawn_y"],
                    "z": updated_dict["spawn_z"]
                },
                "abilities": json.loads(updated_dict["abilities"]) if updated_dict["abilities"] else [],
                "imageUrl": updated_dict.get("image_url")  # Now we can use .get()
            }
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
            db.commit()
            return JSONResponse(npc_data)
            
    except Exception as e:
        logger.error(f"Error updating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/games/current")
async def get_current_game():
    """Get the current active game"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT id, title, slug, description
                FROM games
                WHERE slug = 'game1'  # Default to game1 for now
            """)
            game = cursor.fetchone()
            if game:
                return JSONResponse({
                    "id": game["id"],
                    "title": game["title"],
                    "slug": game["slug"],
                    "description": game["description"]
                })
            return JSONResponse({"error": "No active game found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error getting current game: {str(e)}")
        return JSONResponse({"error": "Failed to get current game"}, status_code=500)

@router.post("/api/assets/create")
async def create_asset(
    request: Request,
    game_id: int = Form(...),
    asset_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        logger.info(f"Creating asset for game {game_id}")
        
        # Get game info
        with get_db() as db:
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            game_slug = game['slug']

            # Delete existing asset if any
            cursor.execute("""
                DELETE FROM assets 
                WHERE asset_id = ? AND game_id = ?
            """, (asset_id, game_id))
            
            # Save file
            game_paths = get_game_paths(game_slug)
            asset_type_dir = type.lower() + 's'
            asset_dir = game_paths['assets'] / asset_type_dir
            asset_dir.mkdir(parents=True, exist_ok=True)
            file_path = asset_dir / f"{asset_id}.rbxm"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Get description using utility
            description_data = await get_asset_description(
                asset_id=asset_id, 
                name=name
            )
            
            logger.info(f"Description data received: {description_data}")
            
            if description_data:
                description = description_data.get('description')
                image_url = description_data.get('imageUrl')
                logger.info(f"Got image URL from description: {image_url}")
            else:
                description = None
                image_url = None
            
            # Create new database entry
            cursor.execute("""
                INSERT INTO assets (
                    game_id, 
                    asset_id, 
                    name, 
                    description, 
                    type,
                    image_url
                ) VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (
                game_id,
                asset_id,
                name,
                description,
                type,
                image_url
            ))
            db_id = cursor.fetchone()['id']
            db.commit()
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
            return JSONResponse({
                "id": db_id,
                "asset_id": asset_id,
                "name": name,
                "description": description,
                "type": type,
                "image_url": image_url,
                "message": "Asset created successfully"
            })
                
    except Exception as e:
        logger.error(f"Error creating asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/npcs")
async def create_npc(
    request: Request,
    game_id: int = Form(...),
    displayName: str = Form(...),
    assetID: str = Form(...),
    system_prompt: str = Form(None),
    responseRadius: int = Form(20),
    spawnX: float = Form(0),  # Individual coordinate fields
    spawnY: float = Form(5),
    spawnZ: float = Form(0),
    abilities: str = Form("[]")
):
    try:
        logger.info(f"Creating NPC for game {game_id}")
        
        # Validate coordinates
        try:
            spawn_x = float(spawnX)
            spawn_y = float(spawnY)
            spawn_z = float(spawnZ)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid spawn coordinates - must be numbers"
            )
        
        with get_db() as db:
            # First check if game exists and get slug
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']  # Get game slug for Lua update

            # Generate a unique NPC ID
            npc_id = str(uuid.uuid4())
            
            # Create NPC record with new coordinate columns
            cursor.execute("""
                INSERT INTO npcs (
                    game_id,
                    npc_id,
                    display_name,
                    asset_id,
                    system_prompt,
                    response_radius,
                    spawn_x,
                    spawn_y,
                    spawn_z,
                    abilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (
                game_id,
                npc_id,
                displayName,
                assetID,
                system_prompt,
                responseRadius,
                spawn_x,
                spawn_y,
                spawn_z,
                abilities
            ))
            db_id = cursor.fetchone()['id']
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
            db.commit()
            
            return JSONResponse({
                "id": db_id,
                "npc_id": npc_id,
                "display_name": displayName,
                "asset_id": assetID,
                "spawn_position": {  # Format for frontend
                    "x": spawn_x,
                    "y": spawn_y,
                    "z": spawn_z
                },
                "message": "NPC created successfully"
            })
            
    except Exception as e:
        logger.error(f"Error creating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/npcs/{npc_id}")
async def delete_npc(npc_id: str, game_id: int):
    try:
        logger.info(f"Deleting NPC {npc_id} from game {game_id}")
        
        with get_db() as db:
            # Get NPC and game info first
            cursor = db.execute("""
                SELECT n.*, g.slug 
                FROM npcs n
                JOIN games g ON n.game_id = g.id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            npc = cursor.fetchone()
            
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            game_slug = npc['slug']  # Get slug from joined query
            
            # Delete the database entry
            cursor.execute("""
                DELETE FROM npcs 
                WHERE npc_id = ? AND game_id = ?
            """, (npc_id, game_id))
            
            db.commit()
            
            # Update Lua files with game_slug
            save_lua_database(game_slug, db)
            
            return JSONResponse({"message": "NPC deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/games/{game_id}/assets/{asset_id}")
async def delete_asset(game_id: int, asset_id: str):
    try:
        logger.info(f"Deleting asset {asset_id} from game {game_id}")
        
        with get_db() as db:
            try:
                # First get game info
                cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                
                game_slug = game['slug']
                
                # Delete any NPCs using this asset
                cursor.execute("""
                    DELETE FROM npcs 
                    WHERE game_id = ? AND asset_id = ?
                """, (game_id, asset_id))
                
                # Delete the asset
                cursor.execute("""
                    DELETE FROM assets 
                    WHERE game_id = ? AND asset_id = ?
                """, (game_id, asset_id))
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Update Lua files
                save_lua_database(game_slug, db)
                
                db.commit()
                return JSONResponse({"message": "Asset deleted successfully"})
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error deleting asset: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update the dashboard_new route
@router.get("/dashboard/new")
async def dashboard_new(request: Request):
    """Render the new version of the dashboard"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            ORDER BY created_at DESC
        """)
        games = cursor.fetchall()
        
    return templates.TemplateResponse(
        "dashboard_new.html", 
        {
            "request": request,
            "games": games
        }
    )

@router.get("/api/games/templates")
async def get_game_templates():
    """Get list of games available for cloning"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT id, title, slug, description 
                FROM games 
                ORDER BY created_at DESC
            """)
            templates = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Found {len(templates)} available templates")
            return JSONResponse({"templates": templates})
            
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ... rest of your existing routes ...




```

### api/app/conversation_manager.py

```py
from datetime import datetime, timedelta

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.expiry_time = timedelta(minutes=30)

    def get_conversation(self, player_id, npc_id):
        key = (player_id, npc_id)
        if key in self.conversations:
            conversation, last_update = self.conversations[key]
            if datetime.now() - last_update > self.expiry_time:
                del self.conversations[key]
                return []
            return conversation
        return []

    def update_conversation(self, player_id, npc_id, message):
        key = (player_id, npc_id)
        if key not in self.conversations:
            self.conversations[key] = ([], datetime.now())
        conversation, _ = self.conversations[key]
        conversation.append(message)
        self.conversations[key] = (conversation[-50:], datetime.now())
```

### api/static/css/dashboard.css

```css
.nav-button-disabled {
    opacity: 0.5;
    cursor: not-allowed;
    position: relative;
}

.nav-button-enabled {
    transition: transform 0.1s ease-in-out;
}

.nav-button-enabled:hover {
    transform: translateY(-1px);
}

[title]:not([title=""]):hover:after {
    content: attr(title);
    position: absolute;
    bottom: -30px;
    left: 50%;
    transform: translateX(-50%);
    padding: 5px 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    z-index: 100;
} 
```

### api/static/js/abilityConfig.js

```js
const ABILITY_CONFIG = [
    {
        id: 'move',
        name: 'Movement',
        icon: 'fas fa-walking',
        description: 'Allows NPC to move around'
    },
    {
        id: 'chat',
        name: 'Chat',
        icon: 'fas fa-comments',
        description: 'Enables conversation with players'
    },
    {
        id: 'trade',
        name: 'Trading',
        icon: 'fas fa-exchange-alt',
        description: 'Allows trading items with players'
    },
    {
        id: 'quest',
        name: 'Quest Giver',
        icon: 'fas fa-scroll',
        description: 'Can give and manage quests'
    },
    {
        id: 'combat',
        name: 'Combat',
        icon: 'fas fa-sword',
        description: 'Enables combat abilities'
    }
];

window.ABILITY_CONFIG = ABILITY_CONFIG;

```

### api/static/js/dashboard.js

```js
function debugLog(title, data) {
    console.log(`=== ${title} ===`);
    console.log(JSON.stringify(data, null, 2));
    console.log('=================');
}

let currentNPCs = [];  // Store loaded NPCs

async function saveNPCEdit(event) {
    event.preventDefault();
    const npcId = document.getElementById('editNpcId').value;

    try {
        if (!currentGame) {
            throw new Error('No game selected');
        }

        const selectedAbilities = Array.from(
            document.querySelectorAll('#editAbilitiesCheckboxes input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            assetId: document.getElementById('editNpcModel').value,
            systemPrompt: document.getElementById('editNpcPrompt').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            abilities: selectedAbilities
        };

        console.log('Sending NPC update:', {
            npcId,
            gameId: currentGame.id,
            data
        });

        const response = await fetch(`/api/npcs/${npcId}?game_id=${currentGame.id}`, {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update NPC');
        }

        closeNPCEditModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Reload NPCs to show changes

    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes: ' + error.message, 'error');
    }
}

function editNPC(npcId) {
    console.log('Edit clicked with ID:', npcId, 'Type:', typeof npcId);
    console.log('Current NPCs:', currentNPCs);
    currentNPCs.forEach(n => {
        console.log('NPC ID:', n.id, 'Type:', typeof n.id);
    });

    try {
        if (!currentGame) {
            showNotification('Please select a game first', 'error');
            return;
        }

        // Find NPC using id instead of npcId and ensure string comparison
        const npc = currentNPCs.find(n => String(n.id) === String(npcId));
        if (!npc) {
            console.error('NPC lookup failed:', {
                lookingFor: npcId,
                availableNPCs: currentNPCs.map(n => ({
                    id: n.id,
                    npcId: n.npcId,
                    displayName: n.displayName
                }))
            });
            throw new Error(`NPC not found: ${npcId}`);
        }
        debugLog('Found NPC to edit', npc);

        // Populate form fields
        document.getElementById('editNpcId').value = npc.id;  // Changed from npcId to id
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcModel').value = npc.assetId;
        document.getElementById('editNpcRadius').value = npc.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npc.systemPrompt || '';

        // Show modal
        const modal = document.getElementById('npcEditModal');
        if (modal) {
            modal.style.display = 'block';
        } else {
            console.error('NPC edit modal not found');
        }
    } catch (error) {
        console.error('Error opening NPC edit modal:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}

// Add this to ensure the function is globally available
window.editNPC = editNPC;
window.deleteNPC = deleteNPC;

function loadNPCs() {
    if (!currentGame) {
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading NPCs for game', {
            gameId: currentGame.id,
            gameSlug: currentGame.slug
        });

        fetch(`/api/npcs?game_id=${currentGame.id}`)
            .then(response => response.json())
            .then(data => {
                currentNPCs = data.npcs;
                debugLog('Loaded NPCs', currentNPCs);

                const npcList = document.getElementById('npcList');
                npcList.innerHTML = '';

                if (!currentNPCs || currentNPCs.length === 0) {
                    npcList.innerHTML = '<p class="text-gray-400 text-center p-4">No NPCs found for this game</p>';
                    return;
                }

                currentNPCs.forEach(npc => {
                    const npcCard = document.createElement('div');
                    npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
                    npcCard.innerHTML = `
                        <div class="aspect-w-16 aspect-h-9 mb-4">
                            <img src="${npc.imageUrl || ''}" 
                                 alt="${npc.displayName}" 
                                 class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                        </div>
                        <h3 class="font-bold text-lg truncate text-gray-100">${npc.displayName}</h3>
                        <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId}</p>
                        <p class="text-sm text-gray-400 mb-2">Model: ${npc.model || 'Default'}</p>
                        <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${npc.systemPrompt || 'No personality defined'}</p>
                        <div class="text-sm text-gray-400 mb-4">
                            <div>Response Radius: ${npc.responseRadius}m</div>
                            <div>Abilities: ${(npc.abilities || []).join(', ') || 'None'}</div>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="editNPC(${npc.id})" 
                                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                                Edit
                            </button>
                            <button onclick="deleteNPC(${npc.id})" 
                                    class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                                Delete
                            </button>
                        </div>
                    `;
                    npcList.appendChild(npcCard);
                });
            });
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading NPCs</p>';
    }

    // Add modal HTML if it doesn't exist
    if (!document.getElementById('npcEditModal')) {
        const modalHTML = `
            <div id="npcEditModal" class="modal">
                <div class="modal-content max-w-2xl">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
                        <button onclick="closeNPCEditModal()"
                            class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
                    </div>
                    <form id="npcEditForm" onsubmit="saveNPCEdit(event)" class="space-y-6">
                        <input type="hidden" id="editNpcId">
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                            <input type="text" id="editNpcDisplayName" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                            <input type="text" id="editNpcModel" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                            <input type="number" id="editNpcRadius" required min="1" max="100"
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                            <textarea id="editNpcPrompt" required rows="4"
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"></textarea>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                            <div id="editAbilitiesCheckboxes" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                                <!-- Will be populated via JavaScript -->
                            </div>
                        </div>
                        <div class="flex justify-end space-x-4 pt-4">
                            <button type="button" onclick="closeNPCEditModal()"
                                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                                Cancel
                            </button>
                            <button type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Make it globally available
window.closeNPCEditModal = closeNPCEditModal;








```

### api/static/js/games.js

```js
class GamesDashboard {
    constructor() {
        console.log('GamesDashboard constructor called');
        this.gamesContainer = document.getElementById('games-container');
        this.gameSelector = document.getElementById('gameSelector');
        this.gameForm = document.getElementById('gameForm');
        console.log('Game selector element:', this.gameSelector);
        this.currentGameId = null;
        this.loadGames();
        this.bindEvents();
    }

    bindEvents() {
        // Bind the form submission
        if (this.gameForm) {
            console.log('Binding form submit event');
            this.gameForm.addEventListener('submit', (event) => {
                event.preventDefault();
                this.createGame(event);
            });
        } else {
            console.error('Game form not found');
        }
    }

    async createGame(event) {
        const form = event.target;
        const formData = new FormData(form);
        
        try {
            console.log('Creating new game...');
            const response = await fetch('/api/games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: formData.get('title'),
                    description: formData.get('description')
                })
            });
            
            if (!response.ok) throw new Error('Failed to create game');
            
            const result = await response.json();
            console.log('Game created:', result);
            
            // Clear form
            form.reset();
            
            // Refresh games list
            await this.loadGames();
            
            // Show success message
            alert('Game created successfully!');
        } catch (error) {
            console.error('Error creating game:', error);
            alert('Failed to create game. Please try again.');
        }
    }

    async loadGames() {
        try {
            console.log('Loading games...');
            const response = await fetch('/api/games');
            const games = await response.json();
            console.log('Raw games response:', games);
            
            if (!Array.isArray(games)) {
                console.error('Games response is not an array:', games);
                return;
            }
            
            console.log('Found', games.length, 'games');
            this.renderGames(games);
        } catch (error) {
            console.error('Failed to load games:', error);
        }
    }

    renderGames(games) {
        console.log('Rendering games:', games);
        if (!this.gamesContainer) {
            console.error('Games container element not found!');
            return;
        }
        
        const html = games.map(game => `
            <div class="bg-dark-800 p-6 rounded-xl shadow-xl">
                <h3 class="text-xl font-bold mb-2 text-blue-400">${game.title}</h3>
                <p class="text-gray-300 mb-4">${game.description || 'No description'}</p>
                <div class="flex space-x-4 text-gray-400 mb-4">
                    <span><i class="fas fa-cube"></i> Assets: ${game.asset_count}</span>
                    <span><i class="fas fa-user"></i> NPCs: ${game.npc_count}</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="gamesDashboard.editGame('${game.slug}')"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="gamesDashboard.deleteGame('${game.slug}')"
                        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
        
        console.log('Generated HTML:', html);
        this.gamesContainer.innerHTML = html;
    }

    async editGame(slug) {
        try {
            // Fetch the game data
            const response = await fetch(`/api/games/${slug}`);
            const game = await response.json();
            
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.style.display = 'block';
            modal.innerHTML = `
                <div class="modal-content">
                    <h2 class="text-xl font-bold mb-4 text-blue-400">Edit Game</h2>
                    <form id="edit-game-form" class="space-y-4">
                        <input type="hidden" id="edit-game-slug" value="${slug}">
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Title</label>
                            <input type="text" id="edit-game-title" value="${game.title}" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Description</label>
                            <textarea id="edit-game-description" required rows="4"
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
                        </div>
                        <div class="flex justify-end space-x-4">
                            <button type="button" onclick="this.closest('.modal').remove()"
                                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">Cancel</button>
                            <button type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Save Changes</button>
                        </div>
                    </form>
                </div>
            `;

            document.body.appendChild(modal);

            document.getElementById('edit-game-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const slug = document.getElementById('edit-game-slug').value;
                const title = document.getElementById('edit-game-title').value;
                const description = document.getElementById('edit-game-description').value;

                try {
                    const response = await fetch(`/api/games/${slug}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ title, description })
                    });

                    if (!response.ok) throw new Error('Failed to update game');
                    
                    await this.loadGames();
                    modal.remove();
                } catch (error) {
                    console.error('Error updating game:', error);
                    alert('Failed to update game. Please try again.');
                }
            });
        } catch (error) {
            console.error('Error editing game:', error);
            alert('Failed to edit game. Please try again.');
        }
    }

    async deleteGame(slug) {
        if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/games/${slug}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete game');
            
            await this.loadGames();
            alert('Game deleted successfully');
        } catch (error) {
            console.error('Error deleting game:', error);
            alert('Failed to delete game. Please try again.');
        }
    }

    async switchGame(gameId) {
        this.currentGameId = gameId;
        if (gameId) {
            // Store selected game ID in localStorage
            localStorage.setItem('currentGameId', gameId);
            
            // Reload assets and NPCs for the selected game
            try {
                // Clear existing lists
                document.getElementById('assetList').innerHTML = '';
                document.getElementById('npcList').innerHTML = '';
                
                // Load assets for selected game
                const assetsResponse = await fetch(`/api/assets?game_id=${gameId}`);
                const assets = await assetsResponse.json();
                renderAssetList(assets);

                // Load NPCs for selected game
                const npcsResponse = await fetch(`/api/npcs?game_id=${gameId}`);
                const npcs = await npcsResponse.json();
                renderNPCList(npcs);
            } catch (error) {
                console.error('Error loading game data:', error);
            }
        } else {
            localStorage.removeItem('currentGameId');
            // Clear lists when no game is selected
            document.getElementById('assetList').innerHTML = '';
            document.getElementById('npcList').innerHTML = '';
        }
    }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing GamesDashboard');
    window.gamesDashboard = new GamesDashboard();
}); 
```

### api/static/js/dashboard_new/abilityConfig.js

```js
const ABILITY_CONFIG = [
    {
        id: 'move',
        name: 'Movement',
        icon: 'fas fa-walking',
        description: 'Allows NPC to move around'
    },
    {
        id: 'chat',
        name: 'Chat',
        icon: 'fas fa-comments',
        description: 'Enables conversation with players'
    },
    {
        id: 'trade',
        name: 'Trading',
        icon: 'fas fa-exchange-alt',
        description: 'Allows trading items with players'
    },
    {
        id: 'quest',
        name: 'Quest Giver',
        icon: 'fas fa-scroll',
        description: 'Can give and manage quests'
    },
    {
        id: 'combat',
        name: 'Combat',
        icon: 'fas fa-sword',
        description: 'Enables combat abilities'
    }
];

window.ABILITY_CONFIG = ABILITY_CONFIG;

```

### api/static/js/dashboard_new/game.js

```js
import { state, updateNavigationState } from './state.js';
import { showNotification } from './ui.js';

export async function selectGame(gameId) {
    try {
        const response = await fetch(`/api/games/${gameId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch game data');
        }
        
        const gameData = await response.json();
        
        // Update state and navigation
        state.currentGame = gameData;
        updateNavigationState();
        
        // Update display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${gameData.title}`;
        }
        
        showNotification('Game selected successfully', 'success');
        
    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification('Failed to select game', 'error');
    }
}

// Make function globally available
window.selectGame = selectGame; 
```

### api/static/js/dashboard_new/npc.js

```js
import { state } from './state.js';
import { showNotification } from './ui.js';
import { showModal } from './ui.js';

// Add version identifier at top
console.log('=== Loading NPC.js v2023-11-22-D ===');

// Add function to fetch available models
async function fetchAvailableModels() {
    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        return data.assets || [];
    } catch (error) {
        console.error('Error fetching models:', error);
        return [];
    }
}

export async function editNPC(npcId) {
    console.log('NPC.JS: editNPC called with:', npcId);
    try {
        // Find NPC using npcId
        const npc = state.currentNPCs.find(n => n.npcId === npcId);
        console.log('NPC data to edit:', npc);

        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }

        // Fetch available models first
        const availableModels = await fetchAvailableModels();
        console.log('Available models:', availableModels);

        // Parse spawn position - handle both string and object formats
        let spawnPosition;
        if (typeof npc.spawnPosition === 'string') {
            spawnPosition = JSON.parse(npc.spawnPosition);
        } else {
            spawnPosition = npc.spawnPosition || { x: 0, y: 5, z: 0 };
        }
        console.log('Parsed spawn position:', spawnPosition);

        // Create modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
            </div>
            <form id="editNPCForm" class="space-y-4">
                <input type="hidden" id="editNpcId" value="${npc.npcId}">
                
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                    <input type="text" id="editNpcDisplayName" value="${npc.displayName || ''}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                    <select id="editNpcModel" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        ${availableModels.map(model => `
                            <option value="${model.assetId}" ${model.assetId === npc.assetId ? 'selected' : ''}>
                                ${model.name}
                            </option>
                        `).join('')}
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                    <input type="number" id="editNpcRadius" value="${npc.responseRadius || 20}" required min="1" max="100"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                    <textarea id="editNpcPrompt" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${npc.systemPrompt || ''}</textarea>
                </div>

                <!-- Add spawn position fields -->
                <div class="grid grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn X:</label>
                        <input type="number" id="editNpcSpawnX" value="${spawnPosition.x}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn Y:</label>
                        <input type="number" id="editNpcSpawnY" value="${spawnPosition.y}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn Z:</label>
                        <input type="number" id="editNpcSpawnZ" value="${spawnPosition.z}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                    <div id="editAbilitiesContainer" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                        ${window.ABILITY_CONFIG.map(ability => `
                            <label class="flex items-center space-x-2">
                                <input type="checkbox" name="abilities" value="${ability.id}"
                                    ${(npc.abilities || []).includes(ability.id) ? 'checked' : ''}
                                    class="form-checkbox h-4 w-4 text-blue-600">
                                <span class="text-gray-300">
                                    <i class="${ability.icon}"></i>
                                    ${ability.name}
                                </span>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="window.hideModal()" 
                        class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                        Cancel
                    </button>
                    <button type="submit" 
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        `;

        // Show modal
        showModal(modalContent);

        // Update form submit handler to include spawn position
        const form = modalContent.querySelector('form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                
                // Get form values
                const formData = {
                    displayName: form.querySelector('#editNpcDisplayName').value.trim(),
                    assetId: form.querySelector('#editNpcModel').value,
                    responseRadius: parseInt(form.querySelector('#editNpcRadius').value) || 20,
                    systemPrompt: form.querySelector('#editNpcPrompt').value.trim(),
                    abilities: Array.from(form.querySelectorAll('input[name="abilities"]:checked')).map(cb => cb.value),
                    // Add spawn position
                    spawnPosition: {
                        x: parseFloat(form.querySelector('#editNpcSpawnX').value) || 0,
                        y: parseFloat(form.querySelector('#editNpcSpawnY').value) || 5,
                        z: parseFloat(form.querySelector('#editNpcSpawnZ').value) || 0
                    }
                };

                console.log('Form data before save:', formData);

                try {
                    const npcUuid = form.querySelector('#editNpcId').value;
                    console.log('Using NPC UUID for save:', npcUuid);
                    await saveNPCEdit(npcUuid, formData);
                } catch (error) {
                    showNotification(error.message, 'error');
                }
            };
        }
    } catch (error) {
        console.error('NPC.JS: Error in editNPC:', error);
        showNotification(error.message, 'error');
    }
}

export async function saveNPCEdit(npcId, data) {
    try {
        console.log('NPC.js v2023-11-22-D: Saving NPC with data:', {
            npcId,
            gameId: state.currentGame.id,
            data
        });

        // Send data directly without additional serialization
        const formattedData = {
            ...data
            // No spawn_position field, just use spawnPosition object
        };

        console.log('Formatted data for backend:', formattedData);

        const response = await fetch(`/api/npcs/${npcId}?game_id=${state.currentGame.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formattedData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update NPC');
        }

        hideModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Refresh the list
    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification(error.message, 'error');
    }
}

// Add this function to populate abilities in the create form
function populateCreateAbilities() {
    const container = document.getElementById('createAbilitiesContainer');
    if (container && window.ABILITY_CONFIG) {
        container.innerHTML = window.ABILITY_CONFIG.map(ability => `
            <label class="flex items-center space-x-2">
                <input type="checkbox" name="abilities" value="${ability.id}"
                    class="form-checkbox h-4 w-4 text-blue-600">
                <span class="text-gray-300">
                    <i class="${ability.icon}"></i>
                    ${ability.name}
                </span>
            </label>
        `).join('');
    }
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', () => {
    populateCreateAbilities();
});

// Make function globally available
window.editNPC = editNPC;
window.saveNPCEdit = saveNPCEdit;
window.populateCreateAbilities = populateCreateAbilities;

export async function createNPC(event) {
    event.preventDefault();
    
    try {
        const form = event.target;
        const formData = new FormData(form);
        formData.set('game_id', state.currentGame.id);

        // Get abilities
        const abilities = Array.from(form.querySelectorAll('input[name="abilities"]:checked'))
            .map(cb => cb.value);
        formData.set('abilities', JSON.stringify(abilities));

        const response = await fetch('/api/npcs', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create NPC');
        }

        showNotification('NPC created successfully', 'success');
        form.reset();
        loadNPCs();  // Refresh the list

    } catch (error) {
        console.error('Error creating NPC:', error);
        showNotification(error.message, 'error');
    }

    return false;  // Prevent form submission
}

// Make function globally available
window.createNPC = createNPC;
```

### api/static/js/dashboard_new/assets.js

```js
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

export async function loadAssets() {
    if (!state.currentGame) {
        console.warn('No game selected');
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}`);
        const data = await response.json();
        
        const assetList = document.getElementById('assetList');
        if (!assetList) return;
        
        assetList.innerHTML = '';
        
        if (data.assets && data.assets.length > 0) {
            data.assets.forEach(asset => {
                const assetCard = document.createElement('div');
                assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
                assetCard.innerHTML = `
                    <div class="aspect-w-16 aspect-h-9 mb-4">
                        <img src="${asset.imageUrl || ''}" 
                             alt="${asset.name}" 
                             class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                    </div>
                    <h3 class="font-bold text-lg mb-2 text-gray-100">${asset.name}</h3>
                    <p class="text-sm text-gray-400 mb-2">ID: ${asset.assetId}</p>
                    <p class="text-sm text-gray-400 mb-4">${asset.description || 'No description'}</p>
                    <div class="flex space-x-2">
                        <button onclick="editAsset('${asset.assetId}')" 
                                class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            Edit
                        </button>
                        <button onclick="deleteAsset('${asset.assetId}')"
                                class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                            Delete
                        </button>
                    </div>
                `;
                assetList.appendChild(assetCard);
            });
        } else {
            assetList.innerHTML = '<p class="text-gray-400">No assets found</p>';
        }
        
        // Update game ID in asset form
        const gameIdInput = document.getElementById('assetFormGameId');
        if (gameIdInput) {
            gameIdInput.value = state.currentGame.id;
        }
        
    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
    }
}

export async function editAsset(assetId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    try {
        // Fetch the asset directly from the API instead of state
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&asset_id=${assetId}`);
        const data = await response.json();
        const asset = data.assets?.[0];  // Get first asset from response

        if (!asset) {
            showNotification('Asset not found', 'error');
            return;
        }

        console.log('Editing asset:', asset); // Debug log

        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Asset</h2>
            </div>
            <form class="space-y-4">
                <input type="hidden" name="assetId" value="${asset.assetId}">
                
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                    <input type="text" name="name" value="${escapeHTML(asset.name)}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <div class="flex items-center space-x-2 mb-1">
                        <label class="block text-sm font-medium text-gray-300">Current Image:</label>
                        <span class="text-sm text-gray-400">${asset.assetId}</span>
                    </div>
                    <img src="${asset.imageUrl}" alt="${escapeHTML(asset.name)}"
                        class="w-full h-48 object-contain rounded-lg border border-dark-600 bg-dark-700 mb-4">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                    <textarea name="description" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${escapeHTML(asset.description || '')}</textarea>
                </div>

                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="window.hideModal()" 
                        class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                        Cancel
                    </button>
                    <button type="submit" 
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        `;

        showModal(modalContent);

        // Add form submit handler
        const form = modalContent.querySelector('form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            // Get form values using form.elements
            const name = form.elements['name'].value.trim();
            const description = form.elements['description'].value.trim();

            console.log('Form values:', { name, description }); // Debug log

            // Validate
            if (!name) {
                showNotification('Name is required', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/games/${state.currentGame.id}/assets/${asset.assetId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, description })
                });

                if (!response.ok) {
                    throw new Error('Failed to update asset');
                }

                hideModal();
                showNotification('Asset updated successfully', 'success');
                loadAssets();  // Refresh the list
            } catch (error) {
                console.error('Error saving asset:', error);
                showNotification('Failed to save changes', 'error');
            }
        };
    } catch (error) {
        console.error('Error editing asset:', error);
        showNotification('Failed to load asset data', 'error');
    }
}

export async function saveAssetEdit(assetId) {
    try {
        // Get form values using the form element
        const form = document.getElementById('editAssetForm');
        const name = form.querySelector('#editAssetName').value.trim();
        const description = form.querySelector('#editAssetDescription').value.trim();

        // Debug log
        console.log('Saving asset with data:', { name, description });

        // Validate
        if (!name) {
            throw new Error('Name is required');
        }

        // Get the original asset to preserve existing data
        const asset = state.currentAssets.find(a => a.assetId === assetId);
        if (!asset) {
            throw new Error('Asset not found');
        }

        // Merge new data with existing data
        const data = {
            name: name || asset.name,
            description: description || asset.description,
            type: asset.type,  // Preserve existing type
            imageUrl: asset.imageUrl  // Preserve existing image URL
        };

        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update asset');
        }

        const result = await response.json();
        console.log('Asset updated:', result);

        hideModal();
        showNotification('Asset updated successfully', 'success');
        loadAssets();  // Refresh the list
    } catch (error) {
        console.error('Error saving asset:', error);
        showNotification(error.message, 'error');
    }
}

export async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }

    try {
        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete asset');
        }

        showNotification('Asset deleted successfully', 'success');
        loadAssets();
    } catch (error) {
        console.error('Error deleting asset:', error);
        showNotification('Failed to delete asset', 'error');
    }
}

export async function createAsset(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const submitBtn = document.getElementById('submitAssetBtn');
    submitBtn.disabled = true;

    try {
        const formData = new FormData(event.target);
        formData.set('game_id', state.currentGame.id);

        debugLog('Submitting asset form with data:', {
            game_id: formData.get('game_id'),
            asset_id: formData.get('asset_id'),
            name: formData.get('name'),
            type: formData.get('type'),
            file: formData.get('file').name
        });

        const response = await fetch('/api/assets/create', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create asset');
        }

        const result = await response.json();
        console.log('Asset created:', result);

        showNotification('Asset created successfully', 'success');
        event.target.reset();
        loadAssets();

    } catch (error) {
        console.error('Error creating asset:', error);
        showNotification(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
    }
}

// Make functions globally available
window.loadAssets = loadAssets;
window.editAsset = editAsset;
window.deleteAsset = deleteAsset;
window.createAsset = createAsset; 

// Helper function to escape HTML
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, (tag) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag]));
} 
```

### api/static/js/dashboard_new/utils.js

```js
export function debugLog(title, data) {
    // You can set this to false in production
    const DEBUG = true;
    
    if (DEBUG) {
        console.log(`=== ${title} ===`);
        console.log(JSON.stringify(data, null, 2));
        console.log('=================');
    }
}

export function validateData(data, schema) {
    // Basic data validation helper
    for (const [key, requirement] of Object.entries(schema)) {
        if (requirement.required && !data[key]) {
            throw new Error(`Missing required field: ${key}`);
        }
    }
    return true;
}

// Make debug functions globally available if needed
window.debugLog = debugLog;

export function validateAsset(data) {
    const required = ['name', 'assetId', 'type'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}

export function validateNPC(data) {
    const required = ['displayName', 'assetId', 'systemPrompt'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}

export function validateNPCData(data) {
    // Required fields
    const required = {
        displayName: 'Display Name',
        assetId: 'Model',
        systemPrompt: 'System Prompt',
        responseRadius: 'Response Radius'
    };

    // Check required fields
    for (const [field, label] of Object.entries(required)) {
        if (!data[field] || data[field] === '') {
            throw new Error(`${label} is required`);
        }
    }

    // Validate response radius
    const radius = parseInt(data.responseRadius);
    if (isNaN(radius) || radius < 1 || radius > 100) {
        throw new Error('Response Radius must be between 1 and 100');
    }

    // Validate abilities array
    if (!Array.isArray(data.abilities)) {
        throw new Error('Invalid abilities format');
    }

    return true;
}

// Make validation function globally available
window.validateNPCData = validateNPCData;
```

### api/static/js/dashboard_new/index.js

```js
// Add at the very top with timestamp
console.log('=== DASHBOARD-NEW-INDEX-2023-11-22-A Loading index.js ===');

// Imports with version check
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';
import { editNPC } from './npc.js';  // Import editNPC

console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Imports loaded:', {
    showNotification: typeof showNotification,
    debugLog: typeof debugLog,
    state: typeof state,
    loadGames: typeof loadGames,
    editNPC: typeof editNPC  // Verify editNPC is imported
});

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Dashboard initialization');
    await loadGames();
});

// Enhanced populateAssetSelector with unique logging
async function populateAssetSelector() {
    console.log('populateAssetSelector called', {
        currentGame: state.currentGame,
        currentTab: state.currentTab
    });

    if (!state.currentGame) {
        console.warn('No game selected, cannot populate asset selector');
        return;
    }

    try {
        // Fetch assets for the current game
        const url = `/api/assets?game_id=${state.currentGame.id}`;
        console.log('Fetching assets from:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        console.log('Received assets:', data);

        // Find and populate the selector
        const assetSelect = document.getElementById('assetSelect');
        if (!assetSelect) {
            console.error('Asset select element not found in DOM');
            return;
        }

        // Clear and populate the selector
        assetSelect.innerHTML = '<option value="">Select a model...</option>';
        if (data.assets && Array.isArray(data.assets)) {
            data.assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.assetId || asset.asset_id;
                option.textContent = asset.name;
                assetSelect.appendChild(option);
            });
            console.log(`Added ${data.assets.length} options to asset selector`);
        }
    } catch (error) {
        console.error('Error populating asset selector:', error);
        throw error; // Propagate error for handling in switchTab
    }
}

// Enhanced tab management with unique logging
window.showTab = function(tabName) {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Tab Change:', {
        from: state.currentTab,
        to: tabName,
        gameId: state.currentGame?.id
    });

    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    const tabElement = document.getElementById(`${tabName}Tab`);
    tabElement.classList.remove('hidden');
    updateCurrentTab(tabName);

    // Load content based on tab
    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        // First load NPCs, then populate the asset selector
        window.loadNPCs().then(() => {
            window.populateAssetSelector();
            console.log('NPCs loaded and asset selector populated');
        }).catch(error => {
            console.error('Error loading NPCs:', error);
        });
    }
};

// Make functions globally available
window.populateAssetSelector = populateAssetSelector;
window.loadNPCs = async function() {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Loading NPCs');
    try {
        const response = await fetch(`/api/npcs?game_id=${state.currentGame.id}`);
        const data = await response.json();
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: NPCs loaded:', data);

        // Store NPCs in state
        state.currentNPCs = data.npcs;

        // Update UI
        const npcList = document.getElementById('npcList');
        if (npcList) {
            npcList.innerHTML = '';
            if (data.npcs && data.npcs.length > 0) {
                data.npcs.forEach(npc => {
                    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Creating NPC card:', npc);
                    const npcCard = document.createElement('div');
                    npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
                    
                    // Parse spawn position
                    let spawnPos;
                    try {
                        spawnPos = typeof npc.spawnPosition === 'string' ? 
                            JSON.parse(npc.spawnPosition) : 
                            npc.spawnPosition || { x: 0, y: 5, z: 0 };
                    } catch (e) {
                        console.error('Error parsing spawn position:', e);
                        spawnPos = { x: 0, y: 5, z: 0 };
                    }

                    // Format abilities with icons
                    const abilityIcons = (npc.abilities || []).map(abilityId => {
                        const ability = window.ABILITY_CONFIG.find(a => a.id === abilityId);
                        return ability ? `<i class="${ability.icon}" title="${ability.name}"></i>` : '';
                    }).join(' ');
                    
                    npcCard.innerHTML = `
                        <div class="aspect-w-16 aspect-h-9 mb-4">
                            <img src="${npc.imageUrl || ''}" 
                                 alt="${npc.displayName}" 
                                 class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                        </div>
                        <h3 class="font-bold text-lg truncate text-gray-100">${npc.displayName}</h3>
                        <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId}</p>
                        <p class="text-sm text-gray-400 mb-2">Model: ${npc.model || 'Default'}</p>
                        <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${npc.systemPrompt || 'No personality defined'}</p>
                        <div class="text-sm text-gray-400 mb-4">
                            <div>Response Radius: ${npc.responseRadius}m</div>
                            <div class="grid grid-cols-3 gap-1 mb-2">
                                <div>X: ${spawnPos.x.toFixed(2)}</div>
                                <div>Y: ${spawnPos.y.toFixed(2)}</div>
                                <div>Z: ${spawnPos.z.toFixed(2)}</div>
                            </div>
                            <div class="text-xl space-x-2">${abilityIcons}</div>
                        </div>
                        <div class="flex space-x-2">
                            <button class="edit-npc-btn flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Edit
                            </button>
                            <button class="delete-npc-btn flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                                Delete
                            </button>
                        </div>
                    `;

                    // Add event listeners
                    const editBtn = npcCard.querySelector('.edit-npc-btn');
                    const deleteBtn = npcCard.querySelector('.delete-npc-btn');

                    editBtn.addEventListener('click', () => {
                        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Edit clicked for NPC:', npc.npcId);
                        window.editNPC = editNPC;
                        editNPC(npc.npcId);
                    });

                    deleteBtn.addEventListener('click', async () => {
                        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Delete clicked for NPC:', npc.npcId);
                        if (confirm(`Are you sure you want to delete NPC "${npc.displayName}"?`)) {
                            try {
                                const response = await fetch(`/api/npcs/${npc.npcId}?game_id=${state.currentGame.id}`, {
                                    method: 'DELETE'
                                });

                                if (!response.ok) {
                                    const error = await response.json();
                                    throw new Error(error.detail || 'Failed to delete NPC');
                                }

                                showNotification('NPC deleted successfully', 'success');
                                loadNPCs();  // Refresh the list
                            } catch (error) {
                                console.error('Error deleting NPC:', error);
                                showNotification(error.message, 'error');
                            }
                        }
                    });

                    npcList.appendChild(npcCard);
                });
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
};

// Add this to verify the function is available
console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Checking global functions:', {
    editNPC: typeof window.editNPC,
    deleteNPC: typeof window.deleteNPC,
    loadNPCs: typeof window.loadNPCs
});

// Tab switching function
function switchTab(tabName) {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Switching to tab:', tabName, {
        currentGame: state.currentGame,
        currentTab: state.currentTab
    });

    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}Tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Update state
    state.currentSection = tabName;
    updateCurrentTab(tabName);

    // Load content based on the tab
    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        console.log('Loading NPCs tab content...');
        
        // First load NPCs
        window.loadNPCs()
            .then(() => {
                console.log('NPCs loaded, populating asset selector...');
                // Then populate the asset selector
                return populateAssetSelector();
            })
            .then(() => {
                console.log('Asset selector populated successfully');
            })
            .catch(error => {
                console.error('Error in NPC tab initialization:', error);
                showNotification('Error loading NPC data', 'error');
            });
    }
}

// Initialize navigation
document.addEventListener('DOMContentLoaded', () => {
    // Set up navigation click handlers
    const navButtons = {
        'nav-games': 'games',
        'nav-assets': 'assets',
        'nav-npcs': 'npcs',
        'nav-players': 'players'
    };
    
    Object.entries(navButtons).forEach(([buttonId, tabName]) => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', () => {
                if (!button.disabled || tabName === 'games') {
                    switchTab(tabName);
                }
            });
        }
    });
    
    // Start with games tab
    switchTab('games');
});

// Make functions globally available
window.switchTab = switchTab;
window.populateAssetSelector = populateAssetSelector;

// Export for module use
export { switchTab };








```

### api/static/js/dashboard_new/games.js

```js
import { state, updateNavigationState } from './state.js';
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { switchTab } from './index.js';

export async function loadGames() {
    try {
        const response = await fetch('/api/games');
        const games = await response.json();
        
        const container = document.getElementById('games-container');
        if (!container) return;
        
        container.innerHTML = '';
        games.forEach(game => {
            const gameCard = createGameCard(game);
            container.appendChild(gameCard);
        });
        
        // Also populate clone selector
        populateCloneSelector(games);
        
    } catch (error) {
        console.error('Error loading games:', error);
        showNotification('Failed to load games', 'error');
    }
}

function createGameCard(game) {
    const card = document.createElement('div');
    card.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
    
    card.innerHTML = `
        <h3 class="font-bold text-lg mb-2 text-gray-100">${game.title}</h3>
        <p class="text-sm text-gray-400 mb-4">${game.description || 'No description'}</p>
        <div class="text-sm text-gray-400 mb-4">
            <div>Assets: ${game.asset_count || 0}</div>
            <div>NPCs: ${game.npc_count || 0}</div>
        </div>
        <div class="flex space-x-2">
            <button onclick="selectGame('${game.slug}')" 
                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Select
            </button>
            <button onclick="editGame('${game.slug}')"
                    class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                Edit
            </button>
            <button onclick="deleteGame('${game.slug}')"
                    class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                Delete
            </button>
        </div>
    `;
    
    return card;
}

export async function selectGame(gameSlug) {
    debugLog('Selecting game', { gameSlug });
    
    try {
        const response = await fetch(`/api/games/${gameSlug}`);
        if (!response.ok) {
            throw new Error('Failed to fetch game data');
        }
        
        const gameData = await response.json();
        console.log('Game selected:', gameData);
        
        // Update state
        state.currentGame = gameData;
        updateNavigationState();
        
        // Update display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${gameData.title}`;
        }
        
        // Load initial data without forcing tab switch
        if (window.loadAssets) {
            await window.loadAssets();
        }
        if (window.loadNPCs) {
            await window.loadNPCs();
        }
        
        showNotification('Game selected successfully', 'success');
        
    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification('Failed to select game', 'error');
    }
}

// Add game creation function
export async function handleGameSubmit(event) {
    event.preventDefault();
    
    try {
        const form = event.target;
        const formData = new FormData(form);
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            cloneFrom: formData.get('cloneFrom')
        };
        
        debugLog('Creating game with data:', data);
        
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create game');
        }

        const result = await response.json();
        showNotification('Game created successfully', 'success');
        form.reset();
        loadGames();  // Refresh the list
        
    } catch (error) {
        console.error('Error creating game:', error);
        showNotification(error.message, 'error');
    }
    
    return false;  // Prevent form submission
}

// Add game deletion function
export async function deleteGame(gameSlug) {
    if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete game');
        }

        showNotification('Game deleted successfully', 'success');
        loadGames();  // Refresh the list
        
        // If this was the current game, reset state
        if (state.currentGame && state.currentGame.slug === gameSlug) {
            state.currentGame = null;
            updateNavigationState();
            const display = document.getElementById('currentGameDisplay');
            if (display) {
                display.textContent = '';
            }
            switchTab('games');
        }
        
    } catch (error) {
        console.error('Error deleting game:', error);
        showNotification(error.message, 'error');
    }
}

// Add edit game function
export async function editGame(gameSlug) {
    try {
        const game = await fetch(`/api/games/${gameSlug}`).then(r => r.json());
        
        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Game</h2>
            </div>
            <form id="editGameForm" class="space-y-4">
                <input type="hidden" name="gameSlug" value="${game.slug}">
                
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Title:</label>
                    <input type="text" name="title" value="${game.title}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                    <textarea name="description" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
                </div>

                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="window.hideModal()" 
                        class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                        Cancel
                    </button>
                    <button type="submit" 
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        `;

        showModal(modalContent);

        // Add form submit handler
        const form = modalContent.querySelector('form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                title: formData.get('title'),
                description: formData.get('description')
            };

            try {
                const response = await fetch(`/api/games/${game.slug}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    throw new Error('Failed to update game');
                }

                hideModal();
                showNotification('Game updated successfully', 'success');
                loadGames();
            } catch (error) {
                console.error('Error updating game:', error);
                showNotification(error.message, 'error');
            }
        };
    } catch (error) {
        console.error('Error editing game:', error);
        showNotification('Failed to load game data', 'error');
    }
}

// Make all functions globally available
window.selectGame = selectGame;
window.loadGames = loadGames;
window.handleGameSubmit = handleGameSubmit;
window.deleteGame = deleteGame;
window.populateCloneSelector = populateCloneSelector;
window.editGame = editGame;

// Add this function
function populateCloneSelector(games) {
    const selector = document.getElementById('cloneFromSelect');
    if (!selector) return;
    
    // Clear existing options except the default
    selector.innerHTML = '<option value="">Empty Game (No Assets)</option>';
    
    // Add games as options
    games.forEach(game => {
        const option = document.createElement('option');
        option.value = game.slug;
        option.textContent = game.title;
        selector.appendChild(option);
    });
} 
```

### api/static/js/dashboard_new/ui.js

```js
import { state } from './state.js';

export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'error' ? 'bg-red-600' :
        type === 'success' ? 'bg-green-600' :
        'bg-blue-600'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 3000);
    }, 3000);
}

export function showModal(content) {
    console.log('UI.JS: showModal called with content:', content);
    
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    console.log('UI.JS: Created backdrop');

    const modal = document.createElement('div');
    modal.className = 'bg-dark-900 rounded-lg shadow-xl max-w-2xl w-full mx-4';
    console.log('UI.JS: Created modal');

    modal.appendChild(content);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    console.log('UI.JS: Added modal to DOM');

    document.body.style.overflow = 'hidden';
}

export function hideModal() {
    const modal = document.querySelector('.fixed.inset-0');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

export function closeAssetEditModal() {
    const modal = document.getElementById('assetEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

export function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

export function initializeTooltips() {
    const tooltipContent = "Please select a game first";
    
    // Add tooltip attributes to disabled nav items
    ['nav-assets', 'nav-npcs', 'nav-players'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.setAttribute('title', tooltipContent);
            // Optional: Add more sophisticated tooltip library initialization here
        }
    });
}

// Call this in your main initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeTooltips();
});

// Make modal functions globally available
window.showModal = showModal;
window.hideModal = hideModal;
window.closeAssetEditModal = closeAssetEditModal;
window.closeNPCEditModal = closeNPCEditModal; 
```

### api/static/js/dashboard_new/state.js

```js
// Create singleton state
const state = {
    currentGame: null,
    currentSection: 'games',
    currentAssets: [],
    currentNPCs: []
};

// Export single instance
export { state };

// State update functions
export function updateCurrentGame(game) {
    state.currentGame = game;
    // Update UI
    const display = document.getElementById('currentGameDisplay');
    if (display) {
        display.textContent = `Current Game: ${game.title}`;
    }
}

export function updateCurrentTab(tab) {
    state.currentTab = tab;
}

export function updateCurrentAssets(assets) {
    state.currentAssets = assets;
}

export function updateCurrentNPCs(npcs) {
    state.currentNPCs = npcs;
}

export function resetState() {
    state.currentGame = null;
    state.currentAssets = [];
    state.currentNPCs = [];
}

// Add navigation state management
export function updateNavigationState() {
    const hasGame = !!state.currentGame;
    
    // Get nav buttons
    const assetNav = document.getElementById('nav-assets');
    const npcNav = document.getElementById('nav-npcs');
    const playerNav = document.getElementById('nav-players');
    
    // Update button states
    [assetNav, npcNav, playerNav].forEach(btn => {
        if (btn) {
            btn.disabled = !hasGame;
            // Update styles
            if (hasGame) {
                btn.classList.remove('text-gray-400');
                btn.classList.add('text-gray-100');
            } else {
                btn.classList.add('text-gray-400');
                btn.classList.remove('text-gray-100');
            }
        }
    });
}

// Update the setCurrentGame function
export function setCurrentGame(game) {
    state.currentGame = game;
    updateNavigationState();
    // ... rest of the existing function
} 
```

### api/routes/games.py

```py
from fastapi import APIRouter, HTTPException
from ..modules.game_creator import GameCreator
from typing import Optional, Dict

router = APIRouter()
game_creator = GameCreator()

@router.post("/games/create/{game_id}")
async def create_game(
    game_id: str,
    config: Optional[Dict] = None,
    destination: Optional[str] = None
):
    try:
        game_path = await game_creator.create_game(
            game_id=game_id,
            config=config,
            destination=destination
        )
        return {
            "status": "success",
            "game_id": game_id,
            "path": str(game_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
```

### api/templates/npc-edit.html

```html
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit NPC</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.js"></script>
</head>

<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h1 class="text-2xl font-bold mb-6">Edit NPC</h1>
            <form id="npcEditForm" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Basic Info -->
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">ID</label>
                            <input type="text" id="id" name="id" class="mt-1 block w-full border rounded-md shadow-sm"
                                readonly>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Display Name</label>
                            <input type="text" id="displayName" name="displayName"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Model Name</label>
                            <input type="text" id="model" name="model"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Asset ID</label>
                            <input type="text" id="assetID" name="assetID"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Response Radius</label>
                            <input type="number" id="responseRadius" name="responseRadius"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                    </div>

                    <!-- Spawn Position and System Prompt -->
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Spawn Position X</label>
                            <input type="number" id="spawnPosition.x" name="spawnPosition.x"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Spawn Position Y</label>
                            <input type="number" id="spawnPosition.y" name="spawnPosition.y"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Spawn Position Z</label>
                            <input type="number" id="spawnPosition.z" name="spawnPosition.z"
                                class="mt-1 block w-full border rounded-md shadow-sm">
                        </div>
                    </div>
                </div>

                <!-- System Prompt - Full Width -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">System Prompt</label>
                    <textarea id="system_prompt" name="system_prompt" rows="6"
                        class="mt-1 block w-full border rounded-md shadow-sm"></textarea>
                </div>

                <!-- Thumbnail Preview -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">NPC Thumbnail</label>
                    <img id="npcThumbnail" src="" alt="NPC Thumbnail" class="mt-2 max-w-xs border rounded-md">
                </div>

                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="window.location.href='/dashboard'"
                        class="px-4 py-2 border rounded-md text-gray-600">Cancel</button>
                    <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Save
                        Changes</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        async function loadNPCData() {
            const urlParams = new URLSearchParams(window.location.search);
            const npcId = urlParams.get('id');
            if (!npcId) return;

            try {
                const response = await fetch(`/api/npcs/${npcId}`);
                const data = await response.json();

                // Populate form fields
                document.getElementById('id').value = data.id;
                document.getElementById('displayName').value = data.displayName;
                document.getElementById('model').value = data.model;
                document.getElementById('assetID').value = data.assetID;
                document.getElementById('responseRadius').value = data.responseRadius;
                document.getElementById('system_prompt').value = data.system_prompt;

                // Spawn position
                document.getElementById('spawnPosition.x').value = data.spawnPosition.x;
                document.getElementById('spawnPosition.y').value = data.spawnPosition.y;
                document.getElementById('spawnPosition.z').value = data.spawnPosition.z;

                // Load thumbnail
                if (data.assetID) {
                    const thumbnailResponse = await fetch(`/api/asset-thumbnail/${data.assetID}`);
                    const thumbnailData = await thumbnailResponse.json();
                    document.getElementById('npcThumbnail').src = thumbnailData.imageUrl;
                }
            } catch (error) {
                console.error('Error loading NPC data:', error);
                alert('Failed to load NPC data');
            }
        }

        document.getElementById('npcEditForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                id: document.getElementById('id').value,
                displayName: document.getElementById('displayName').value,
                model: document.getElementById('model').value,
                assetID: document.getElementById('assetID').value,
                responseRadius: parseInt(document.getElementById('responseRadius').value),
                system_prompt: document.getElementById('system_prompt').value,
                spawnPosition: {
                    x: parseFloat(document.getElementById('spawnPosition.x').value),
                    y: parseFloat(document.getElementById('spawnPosition.y').value),
                    z: parseFloat(document.getElementById('spawnPosition.z').value)
                }
            };

            try {
                const response = await fetch(`/api/npcs/${formData.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) throw new Error('Failed to update NPC');

                window.location.href = '/dashboard';
            } catch (error) {
                console.error('Error saving NPC data:', error);
                alert('Failed to save NPC data');
            }
        });

        // Load NPC data when page loads
        loadNPCData();
    </script>
</body>

</html>
```

### api/templates/npcs.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NPC Management</title>
    <!-- Load React -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js" crossorigin></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js" crossorigin></script>
    <!-- Load Babel -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js"></script>
    <!-- Load Tailwind CSS -->
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect } = React;

        const NPCManagement = () => {
            const [npcs, setNPCs] = useState([]);
            const [loading, setLoading] = useState(true);
            const [error, setError] = useState(null);
            const [selectedNPC, setSelectedNPC] = useState(null);
            const [editMode, setEditMode] = useState(false);
            const [showDetails, setShowDetails] = useState(false);
            const [editedNPC, setEditedNPC] = useState(null);

            useEffect(() => {
                fetchNPCs();
            }, []);

            const fetchNPCs = async () => {
                try {
                    const response = await fetch('/api/npcs');
                    if (!response.ok) throw new Error('Failed to fetch NPCs');
                    const data = await response.json();
                    setNPCs(data.npcs);
                    setLoading(false);
                } catch (err) {
                    setError(err.message);
                    setLoading(false);
                }
            };

            const handleEdit = (npc) => {
                setEditedNPC({...npc});
                setEditMode(true);
            };

            const handleSave = async () => {
                try {
                    const response = await fetch(`/api/npcs/${editedNPC.id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(editedNPC),
                    });

                    if (!response.ok) throw new Error('Failed to update NPC');
                    
                    await fetchNPCs();
                    setEditMode(false);
                    setEditedNPC(null);
                } catch (err) {
                    console.error('Error saving NPC:', err);
                    alert('Failed to save NPC: ' + err.message);
                }
            };

            const handleDelete = async (id) => {
                if (!confirm('Are you sure you want to delete this NPC?')) return;
                
                try {
                    const response = await fetch(`/api/npcs/${id}`, {
                        method: 'DELETE',
                    });

                    if (!response.ok) throw new Error('Failed to delete NPC');
                    
                    await fetchNPCs();
                } catch (err) {
                    console.error('Error deleting NPC:', err);
                    alert('Failed to delete NPC: ' + err.message);
                }
            };

            const handleShowDetails = (npc) => {
                setSelectedNPC(npc);
                setShowDetails(true);
            };

            if (loading) return <div className="p-4">Loading...</div>;
            if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

            return (
                <div className="container mx-auto p-4">
                    <h1 className="text-2xl font-bold mb-6">NPC Management</h1>
                    
                    <div className="bg-white shadow-md rounded-lg overflow-hidden">
                        <table className="min-w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Display Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {npcs.map(npc => (
                                    <tr key={npc.id}>
                                        <td className="px-6 py-4 whitespace-nowrap">{npc.id}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">{npc.displayName}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">{npc.assetID}</td>
                                        <td className="px-6 py-4">
                                            <div className="max-w-xs truncate">{npc.description || npc.system_prompt}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <button
                                                onClick={() => handleEdit(npc)}
                                                className="text-blue-600 hover:text-blue-900 mr-2"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleShowDetails(npc)}
                                                className="text-green-600 hover:text-green-900 mr-2"
                                            >
                                                Details
                                            </button>
                                            <button
                                                onClick={() => handleDelete(npc.id)}
                                                className="text-red-600 hover:text-red-900"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Edit Modal */}
                    {editMode && editedNPC && (
                        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
                            <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
                                <h2 className="text-xl font-bold mb-4">Edit NPC</h2>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Display Name</label>
                                        <input
                                            type="text"
                                            value={editedNPC.displayName}
                                            onChange={e => setEditedNPC({...editedNPC, displayName: e.target.value})}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Asset ID</label>
                                        <input
                                            type="text"
                                            value={editedNPC.assetID}
                                            onChange={e => setEditedNPC({...editedNPC, assetID: e.target.value})}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Description</label>
                                        <textarea
                                            value={editedNPC.description || editedNPC.system_prompt}
                                            onChange={e => setEditedNPC({
                                                ...editedNPC,
                                                description: e.target.value,
                                                system_prompt: e.target.value
                                            })}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                            rows="4"
                                        />
                                    </div>
                                </div>
                                <div className="mt-6 flex justify-end space-x-3">
                                    <button
                                        onClick={() => {
                                            setEditMode(false);
                                            setEditedNPC(null);
                                        }}
                                        className="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                    >
                                        Save
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Details Modal */}
                    {showDetails && selectedNPC && (
                        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
                            <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
                                <h2 className="text-xl font-bold mb-4">NPC Details</h2>
                                <div className="space-y-4">
                                    {Object.entries(selectedNPC).map(([key, value]) => (
                                        <div key={key}>
                                            <label className="block text-sm font-medium text-gray-700 capitalize">
                                                {key.replace(/([A-Z])/g, ' $1').trim()}
                                            </label>
                                            <div className="mt-1 text-gray-900">
                                                {typeof value === 'object' 
                                                    ? JSON.stringify(value, null, 2)
                                                    : String(value)
                                                }
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="mt-6 flex justify-end">
                                    <button
                                        onClick={() => {
                                            setShowDetails(false);
                                            setSelectedNPC(null);
                                        }}
                                        className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        };

        // Mount the React app
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(NPCManagement));
    </script>
</body>
</html>

```

### api/templates/players.html

```html
<!DOCTYPE html>
<html lang="en">
<!-- [Previous head and body content remains the same until the script section] -->

    <script>
        // Fetch Player data
        fetch('/api/players')
            .then(response => response.json())
            .then(data => {
                displayPlayers(data.players);
            })
            .catch(error => console.error('Error:', error));

        // Display Players in the table
        function displayPlayers(players) {
            const tableBody = document.getElementById('playerTableBody');
            tableBody.innerHTML = ''; // Clear existing content
            players.forEach(player => {
                const row = document.createElement('tr');
                row.className = 'bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600';
                row.innerHTML = `
                    <td class="py-4 px-6">${player.playerID}</td>
                    <td class="py-4 px-6">${player.displayName}</td>
                    <td class="py-4 px-6">${player.description || ''}</td>
                    <td class="py-4 px-6">${player.imageURL || ''}</td>
                    <td class="py-4 px-6">
                        <button onclick="showEditPlayerModal('${player.playerID}', '${player.displayName}', '${player.description || ''}', '${player.imageURL || ''}')" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</button>
                        <button onclick="deletePlayer('${player.playerID}')" class="font-medium text-red-600 dark:text-red-500 hover:underline ml-2">Delete</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }

        // Show Add Player Modal
        function showAddPlayerModal() {
            document.getElementById('addPlayerModal').classList.remove('hidden');
        }

        // Hide Add Player Modal
        function hideAddPlayerModal() {
            document.getElementById('addPlayerModal').classList.add('hidden');
        }

        // Add Player function
        function addPlayer() {
            const playerData = {
                playerID: document.getElementById('addPlayerID').value,
                displayName: document.getElementById('addDisplayName').value,
                imageURL: document.getElementById('addImageURL').value,
                description: document.getElementById('addDescription').value
            };

            fetch('/api/players', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(playerData),
            })
            .then(response => response.json())
            .then(data => {
                hideAddPlayerModal();
                location.reload();
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Failed to add player');
            });
        }

        // Delete Player function
        function deletePlayer(id) {
            if (confirm('Are you sure you want to delete this player?')) {
                fetch(`/api/players/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        location.reload();
                    })
                    .catch(error => console.error('Error:', error));
            }
        }

        // Show Edit Player Modal
        function showEditPlayerModal(id, displayName, description, imageURL) {
            document.getElementById('editPlayerID').value = id;
            document.getElementById('editDisplayName').value = displayName;
            document.getElementById('editDescription').value = description;
            document.getElementById('editImageURL').value = imageURL;
            document.getElementById('editPlayerModal').classList.remove('hidden');
        }

        // Hide Edit Player Modal
        function hideEditPlayerModal() {
            document.getElementById('editPlayerModal').classList.add('hidden');
        }

        // Save Edited Player
        function saveEditedPlayer() {
            const id = document.getElementById('editPlayerID').value;
            const playerData = {
                playerID: id,
                displayName: document.getElementById('editDisplayName').value,
                description: document.getElementById('editDescription').value,
                imageURL: document.getElementById('editImageURL').value
            };

            fetch(`/api/players/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(playerData),
            })
            .then(response => response.json())
            .then(data => {
                hideEditPlayerModal();
                location.reload();
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Failed to edit player');
            });
        }

        // Theme toggle functionality
        const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
        const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

        if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            themeToggleLightIcon.classList.remove('hidden');
        } else {
            themeToggleDarkIcon.classList.remove('hidden');
        }

        const themeToggleBtn = document.getElementById('theme-toggle');

        themeToggleBtn.addEventListener('click', function() {
            themeToggleDarkIcon.classList.toggle('hidden');
            themeToggleLightIcon.classList.toggle('hidden');

            if (localStorage.getItem('color-theme')) {
                if (localStorage.getItem('color-theme') === 'light') {
                    document.documentElement.classList.add('dark');
                    localStorage.setItem('color-theme', 'dark');
                } else {
                    document.documentElement.classList.remove('dark');
                    localStorage.setItem('color-theme', 'light');
                }
            } else {
                if (document.documentElement.classList.contains('dark')) {
                    document.documentElement.classList.remove('dark');
                    localStorage.setItem('color-theme', 'light');
                } else {
                    document.documentElement.classList.add('dark');
                    localStorage.setItem('color-theme', 'dark');
                }
            }
        });
    </script>
</body>
</html>

```

### api/templates/dashboard_new.html

```html
<!DOCTYPE html>
<html lang="en" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roblox Asset Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        dark: {
                            50: '#f9fafb',
                            100: '#f3f4f6',
                            200: '#e5e7eb',
                            300: '#d1d5db',
                            400: '#9ca3af',
                            500: '#6b7280',
                            600: '#4b5563',
                            700: '#374151',
                            800: '#1f2937',
                            900: '#111827',
                        },
                    },
                },
            },
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
        }

        .modal-content {
            background-color: #1f2937;
            margin: 5% auto;
            padding: 2rem;
            border: 1px solid #374151;
            width: 90%;
            max-width: 600px;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }

        .notification {
            transition: opacity 0.3s ease-in-out;
        }

        /* Modern scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1f2937;
        }

        ::-webkit-scrollbar-thumb {
            background: #4b5563;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #6b7280;
        }
    </style>
    <!-- <script src="/static/js/games.js" defer></script> -->
</head>

<body class="bg-dark-900 text-gray-100 min-h-screen font-sans">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-4xl font-bold mb-6 text-blue-400">Roblox Asset Manager (New Version)</h1>
            <div class="mb-6 bg-dark-800 p-4 rounded-xl shadow-xl">
                <div id="currentGameDisplay" class="text-xl font-semibold text-gray-300">
                    <!-- Will be populated by JS -->
                </div>
            </div>
            <nav class="flex space-x-4 mb-6">
                <button id="nav-games" 
                        class="px-4 py-2 rounded-lg bg-dark-700 text-gray-100 hover:bg-dark-600 transition-colors">
                    Games
                </button>
                <button id="nav-assets" 
                        class="px-4 py-2 rounded-lg bg-dark-700 text-gray-400 hover:bg-dark-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled>
                    Assets
                </button>
                <button id="nav-npcs" 
                        class="px-4 py-2 rounded-lg bg-dark-700 text-gray-400 hover:bg-dark-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled>
                    NPCs
                </button>
                <button id="nav-players" 
                        class="px-4 py-2 rounded-lg bg-dark-700 text-gray-400 hover:bg-dark-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled>
                    Players
                </button>
            </nav>
        </div>

        <!-- Asset Tab -->
        <div id="assetsTab" class="tab-content hidden">
            <div class="mb-8 bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New Asset</h2>
                <form id="assetForm" class="space-y-4" enctype="multipart/form-data" onsubmit="createAsset(event)">
                    <input type="hidden" name="game_id" id="assetFormGameId">
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Asset ID:</label>
                        <input type="text" name="asset_id" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                        <input type="text" name="name" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Type:</label>
                        <select name="type" required
                            class="w-full p-3 bg-dark-700 text-gray-200 rounded-lg">
                            <option value="NPC">NPC</option>
                            <option value="Vehicle">Vehicle</option>
                            <option value="Building">Building</option>
                            <option value="Prop">Prop</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Asset File (.rbxm):</label>
                        <input type="file" name="file" accept=".rbxm,.rbxmx" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <button type="submit" id="submitAssetBtn" class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Add Asset
                    </button>
                </form>
            </div>

            <div>
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Asset List</h2>
                <div id="assetList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Assets will be loaded here -->
                </div>
            </div>
        </div>

        <!-- NPCs Tab -->
        <div id="npcsTab" class="tab-content hidden">
            <div class="mb-8 bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New NPC</h2>
                <form id="createNPCForm" method="POST" action="/api/npcs" class="space-y-6" onsubmit="return createNPC(event)">
                    <input type="hidden" name="game_id" :value="currentGame?.id">
                    
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2 text-gray-300">Display Name</label>
                        <input type="text" name="displayName" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2 text-gray-300">Asset</label>
                        <select id="assetSelect" name="assetID" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">Select a model...</option>
                        </select>
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2 text-gray-300">System Prompt</label>
                        <textarea name="system_prompt" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter NPC's personality and behavior description"></textarea>
                    </div>

                    <div class="grid grid-cols-3 gap-4 mb-4">
                        <div>
                            <label class="text-xs text-gray-400">X</label>
                            <input type="number" name="spawnX" value="0" step="0.1" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        </div>
                        <div>
                            <label class="text-xs text-gray-400">Y</label>
                            <input type="number" name="spawnY" value="5" step="0.1" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        </div>
                        <div>
                            <label class="text-xs text-gray-400">Z</label>
                            <input type="number" name="spawnZ" value="0" step="0.1" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        </div>
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2 text-gray-300">Abilities</label>
                        <div id="createAbilitiesContainer" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                            <!-- Will be populated via JavaScript -->
                        </div>
                    </div>

                    <button type="submit"
                        class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                        Add NPC
                    </button>
                </form>
            </div>

            <div>
                <h2 class="text-2xl font-bold mb-4 text-blue-400">NPC List</h2>
                <div id="npcList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- NPCs will be loaded here -->
                </div>
            </div>
        </div>

        <!-- Players Tab -->
        <div id="playersTab" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-4 text-blue-400">Players</h2>
            <div id="playerList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Players will be loaded here -->
            </div>
        </div>

        <!-- Games Tab -->
        <div id="gamesTab" class="tab-content">
            <div class="mb-8">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Game List</h2>
                <div id="games-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Games will be loaded here -->
                </div>
            </div>

            <div class="bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New Game</h2>
                <form id="gameForm" onsubmit="return handleGameSubmit(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Game Title:</label>
                        <input type="text" name="title" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                        <textarea name="description" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"
                            placeholder="Enter game description..."></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Clone From:</label>
                        <select name="cloneFrom" id="cloneFromSelect" class="w-full p-3 bg-dark-700 text-gray-200 rounded-lg">
                            <option value="">Empty Game (No Assets)</option>
                        </select>
                    </div>
                    <button type="submit"
                        class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Add Game
                    </button>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <h2 class="text-xl font-bold mb-4 text-blue-400">Edit Description</h2>
            <form id="editForm" onsubmit="saveEdit(event)" class="space-y-4">
                <input type="hidden" id="editItemId">
                <input type="hidden" id="editItemType">
                <textarea id="editDescription"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="6"></textarea>
                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Save
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- NPC Edit Modal -->
    <div id="npcEditModal" class="modal">
        <div class="modal-content max-w-2xl">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
                <button onclick="closeNPCEditModal()"
                    class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
            </div>
            <form id="npcEditForm" onsubmit="saveNPCEdit(event)" class="space-y-6">
                <input type="hidden" id="editNpcId">

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                    <input type="text" id="editNpcDisplayName" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                    <select id="editNpcModel" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        <!-- Will be populated dynamically -->
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                    <input type="number" id="editNpcRadius" required min="1" max="100"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Personality:</label>
                    <textarea id="editNpcPrompt" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"></textarea>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                    <div id="editAbilitiesCheckboxes" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                        <!-- Checkboxes will be populated via JavaScript -->
                    </div>
                </div>

                <div class="flex justify-end space-x-4 pt-4">
                    <button type="button" onclick="closeNPCEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Asset Edit Modal -->
    <div id="assetEditModal" class="modal">
        <div class="modal-content max-w-2xl">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Asset</h2>
                <button onclick="closeAssetEditModal()"
                    class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
            </div>
            <form id="assetEditForm" onsubmit="saveAssetEdit(event)" class="space-y-6">
                <input type="hidden" id="editAssetId">

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                    <input type="text" id="editAssetName" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                </div>

                <div>
                    <div class="flex items-center space-x-2 mb-1">
                        <label class="block text-sm font-medium text-gray-300">Current Image:</label>
                        <span id="editAssetId_display" class="text-sm text-gray-400"></span>
                    </div>
                    <img id="editAssetImage"
                        class="w-full h-48 object-contain rounded-lg border border-dark-600 bg-dark-700 mb-4">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                    <textarea id="editAssetDescription" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"></textarea>
                </div>

                <div class="flex justify-end space-x-4 pt-4">
                    <button type="button" onclick="closeAssetEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Add game management modal -->
    <div id="gameModal" class="modal">
        <div class="modal-content">
            <h2>Create New Game</h2>
            <form id="gameForm">
                <input type="text" name="name" placeholder="Game Name" required>
                <input type="text" name="slug" placeholder="URL Slug" required>
                <textarea name="description" placeholder="Description"></textarea>
                <button type="submit">Create Game</button>
            </form>
        </div>
    </div>

    <script src="/static/js/dashboard_new/abilityConfig.js"></script>
    <script type="module" src="/static/js/dashboard_new/utils.js"></script>
    <script type="module" src="/static/js/dashboard_new/ui.js"></script>
    <script type="module" src="/static/js/dashboard_new/state.js"></script>
    <script type="module" src="/static/js/dashboard_new/games.js"></script>
    <script type="module" src="/static/js/dashboard_new/assets.js"></script>
    <script type="module" src="/static/js/dashboard_new/npc.js"></script>
    <script type="module" src="/static/js/dashboard_new/index.js?v=2023-11-22-A"></script>
</body>

</html>

```

### api/db/schema.sql

```sql
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

```

### api/db/migrate.py

```py
import sqlite3
import json
from pathlib import Path
from ..config import DB_DIR, SQLITE_DB_PATH
from ..utils import get_database_paths, load_json_database

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(SQLITE_DB_PATH) as db:
        with open(Path(__file__).parent / 'schema.sql') as f:
            db.executescript(f.read())

def migrate_existing_data():
    """Migrate existing JSON data to SQLite"""
    with sqlite3.connect(SQLITE_DB_PATH) as db:
        # Get the default game
        cursor = db.execute("SELECT id FROM games WHERE slug = 'default-game'")
        default_game = cursor.fetchone()
        
        if not default_game:
            print("Error: Default game not found")
            return
            
        default_game_id = default_game[0]
        
        # Load existing JSON data
        db_paths = get_database_paths()
        
        try:
            # Migrate assets
            asset_data = load_json_database(db_paths['asset']['json'])
            print(f"Found {len(asset_data.get('assets', []))} assets to migrate")
            
            for asset in asset_data.get('assets', []):
                db.execute("""
                    INSERT OR IGNORE INTO assets 
                    (asset_id, name, description, image_url, type, tags, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset['assetId'],
                    asset['name'],
                    asset.get('description', ''),
                    asset.get('imageUrl', ''),
                    asset.get('type', 'unknown'),
                    json.dumps(asset.get('tags', [])),
                    default_game_id
                ))
                print(f"Migrated asset: {asset['name']}")
            
            # Migrate NPCs
            npc_data = load_json_database(db_paths['npc']['json'])
            print(f"Found {len(npc_data.get('npcs', []))} NPCs to migrate")
            
            for npc in npc_data.get('npcs', []):
                db.execute("""
                    INSERT OR IGNORE INTO npcs 
                    (npc_id, display_name, asset_id, model, system_prompt, 
                     response_radius, spawn_position, abilities, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    npc['id'],
                    npc['displayName'],
                    npc['assetId'],
                    npc.get('model', ''),
                    npc.get('system_prompt', ''),
                    npc.get('responseRadius', 20),
                    json.dumps(npc.get('spawnPosition', {})),
                    json.dumps(npc.get('abilities', [])),
                    default_game_id
                ))
                print(f"Migrated NPC: {npc['displayName']}")
            
            db.commit()
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.rollback()
            raise 
```

### api/modules/game_creator.py

```py
from pathlib import Path
from typing import Optional, Dict
import shutil
import json

class GameCreator:
    def __init__(self, template_root: str = None):
        self.template_root = Path(template_root) if template_root else Path(__file__).parent.parent.parent / "templates" / "game_template"
        self.required_structure = {
            "directories": [
                "src/client",
                "src/server",
                "src/shared",
                "src/data",
                "src/services",
                "src/config",
                "src/debug"
            ],
            "files": [
                "default.project.json",
                "src/init.lua",
                "src/config/GameConfig.lua",
                "src/data/NPCDatabase.lua"
            ]
        }

    async def create_game(self, 
                         game_id: str, 
                         config: Dict = None, 
                         destination: Optional[str] = None) -> Path:
        """
        Create a new game from template
        
        Args:
            game_id: Unique identifier for the game
            config: Optional configuration overrides
            destination: Optional destination path
        """
        # Determine destination path
        dest_path = Path(destination) if destination else Path("games") / str(game_id)
        dest_path.mkdir(parents=True, exist_ok=True)

        # Validate template
        await self._validate_template()

        # Copy template
        await self._copy_template(dest_path)

        # Update configuration
        if config:
            await self._update_config(dest_path, game_id, config)

        return dest_path

    async def _validate_template(self):
        """Validate template structure exists"""
        missing = []
        
        for dir_path in self.required_structure["directories"]:
            if not (self.template_root / dir_path).exists():
                missing.append(f"Directory: {dir_path}")
                
        for file_path in self.required_structure["files"]:
            if not (self.template_root / file_path).exists():
                missing.append(f"File: {file_path}")
                
        if missing:
            raise ValueError(f"Invalid template structure. Missing:\n" + "\n".join(missing))

    async def _copy_template(self, destination: Path):
        """Copy template files to destination"""
        def _ignore_patterns(path, names):
            return [n for n in names if n.startswith('.') or n.startswith('__')]
            
        shutil.copytree(self.template_root, destination, 
                       dirs_exist_ok=True, 
                       ignore=_ignore_patterns)

    async def _update_config(self, game_path: Path, game_id: str, config: Dict):
        """Update game configuration"""
        config_path = game_path / "default.project.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                base_config = json.load(f)
            
            # Update with provided config
            base_config.update({
                "name": f"game_{game_id}",
                **config
            })
            
            with open(config_path, 'w') as f:
                json.dump(base_config, f, indent=2) 
```

### api/initial_data/game1/src/data/NPCDatabase.json

```json
{
    "npcs": [
        {
            "id": "oz1",
            "displayName": "Oz the First",
            "assetId": "1388902922",
            "responseRadius": 20,
            "spawnPosition": {
                "x": 20,
                "y": 5,
                "z": 20
            },
            "system_prompt": "You are a wise and mysterious ancient entity. You speak with authority and have knowledge of ancient secrets.",
            "shortTermMemory": [],
            "abilities": [
                "follow",
                "inspect",
                "cast_spell",
                "teach"
            ],
            "model": "old_wizard"
        }
    ]
}
```

### api/initial_data/game1/src/data/AssetDatabase.json

```json
{
    "assets": [
        {
            "assetId": "15571098041",
            "model": "tesla_cybertruck",
            "name": "Tesla Cybertruck",
            "description": "This vehicle features a flat metal, futuristic, angular vehicle reminiscent of a cybertruck. It has a sleek, gray body with distinct sharp edges and minimalistic design. Prominent characteristics include a wide, illuminated front strip, large wheel wells, and a spacious, open cabin. The overall appearance suggests a robust, modern aesthetic.",
            "imageUrl": "https://tr.rbxcdn.com/180DAY-e30fdf43661440a435b6e64373fb3850/420/420/Model/Png/noFilter",
            "type": "vehicle",
            "tags": [
                "futuristic",
                "angular",
                "modern",
                "car",
                "electric"
            ]
        }
    ]
}
```
