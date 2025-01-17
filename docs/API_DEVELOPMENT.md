# Roblox API Development Documentation

## Project Structure
```
api/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py              # Application entry point and FastAPI setup
│   ├── config.py            # Configuration settings and path management
│   ├── database.py          # Database operations and SQLite management
│   ├── db.py               # Database connection utilities (to be consolidated)
│   ├── conversation_manager.py # Chat conversation state management
│   ├── dashboard_router.py   # Dashboard API endpoints
│   ├── routers.py           # Main API endpoints for NPC interactions
│   ├── storage.py           # File storage management
│   ├── utils.py             # Utility functions
│   └── image_utils.py       # Image processing and AI description generation
```

## Core Components

### 1. Application Entry (`main.py`)
- FastAPI application initialization
- CORS middleware setup
- Route registration
- Static file serving
- Error handling

### 2. Configuration (`config.py`)
- Environment variable management
- Directory path configurations
- Game-specific path management
- NPC system prompt configurations

### 3. Database Management
Currently split between:
- `database.py`: Main database operations (CRUD)
- `db.py`: Connection management with logging
- **TODO**: Consolidate into single module

### 4. API Routes
Two main router files:
- `routers.py`: 
  - NPC chat endpoints
  - Asset management
  - Player descriptions
  - OpenAI integration

- `dashboard_router.py`:
  - Game management
  - Asset CRUD operations
  - NPC CRUD operations
  - File uploads

### 5. Storage Management (`storage.py`)
- File storage operations
- Asset file management
- Image storage
- Directory structure maintenance

## Database Schema

### Games Table
```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Assets Table
```sql
CREATE TABLE assets (
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
```

### NPCs Table
```sql
CREATE TABLE npcs (
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
```

## Known Issues

1. Circular Import:
   - Between `database.py` and `utils.py`
   - **Solution**: Move shared functionality to new module

2. Duplicate Database Management:
   - Connection handling in both `db.py` and `database.py`
   - **Solution**: Consolidate into `database.py`

3. Redundant Image Processing:
   - Functions split between `routers.py` and `image_utils.py`
   - **Solution**: Move all image processing to `image_utils.py`

## Required Environment Variables
```
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
```

## Future Improvements

1. Database Management
   - Consolidate database connection handling
   - Implement proper migrations
   - Add connection pooling
   - Improve error handling

2. Code Organization
   - Implement proper package initialization
   - Centralize environment variable handling
   - Remove redundant code
   - Add comprehensive logging

3. Testing
   - Add unit tests
   - Implement integration tests
   - Add API endpoint tests
   - Create test database fixtures

4. Documentation
   - Add API documentation
   - Create endpoint usage guides
   - Document database schema
   - Add setup instructions

## Development Guidelines

1. Code Style
   - Follow PEP 8
   - Use type hints
   - Add docstrings
   - Keep functions focused

2. Error Handling
   - Use custom exceptions
   - Add proper logging
   - Return appropriate status codes
   - Provide meaningful error messages

3. Database Operations
   - Use transactions where appropriate
   - Handle connection cleanup
   - Validate data before operations
   - Use proper indexing

4. File Operations
   - Handle paths securely
   - Clean up temporary files
   - Validate file types
   - Use proper permissions

## Deployment Notes

1. Directory Structure
   - Ensure proper permissions
   - Create required directories
   - Set up logging directory
   - Configure static files

2. Database Setup
   - Run migrations
   - Create initial data
   - Set up backups
   - Configure indexes

3. Environment
   - Set environment variables
   - Configure CORS
   - Set up SSL
   - Configure rate limiting

4. Monitoring
   - Set up logging
   - Configure error tracking
   - Monitor performance
   - Set up alerts 

# NPC Spawn Position Issues

## Problem Description
The NPC spawn position data is not being reliably handled in the frontend/backend flow, despite working in Lua exports.

### Current Issues:
1. Spawn positions not displayed in dashboard
2. Create/edit operations not storing positions
3. Database JSON serialization inconsistencies
4. Frontend/backend field name mismatches

### Current Implementation:
```sql
-- Current schema
CREATE TABLE npcs (
    ...
    spawn_position TEXT,  -- JSON object {"x": 0, "y": 5, "z": 0}
    ...
);
```

```python
# Current backend serialization
spawn_position = json.dumps({
    "x": spawnX,
    "y": spawnY,
    "z": spawnZ
})
```

```javascript
// Current frontend handling
const spawnPosition = {
    x: parseFloat(form.querySelector('[name="spawnX"]').value),
    y: parseFloat(form.querySelector('[name="spawnY"]').value),
    z: parseFloat(form.querySelector('[name="spawnZ"]').value)
};
```

## Root Cause Analysis

1. Data Flow Issues:
   - Frontend sends individual x,y,z values
   - Backend expects JSON object
   - Database stores serialized JSON string
   - Lua export parses and reformats

2. Serialization Problems:
   - Double JSON serialization occurring
   - Inconsistent field naming (spawnPosition vs spawn_position)
   - Missing validation of coordinate values
   - No type enforcement for coordinates

3. Display Issues:
   - Frontend not parsing stored JSON
   - Missing coordinate extraction
   - Form population failures
   - Default values not applied

## Proposed Solutions

### 1. Schema Change Approach
```sql
-- New schema with explicit columns
ALTER TABLE npcs ADD COLUMN spawn_x REAL DEFAULT 0;
ALTER TABLE npcs ADD COLUMN spawn_y REAL DEFAULT 5;
ALTER TABLE npcs ADD COLUMN spawn_z REAL DEFAULT 0;
-- Later: ALTER TABLE npcs DROP COLUMN spawn_position;
```

Benefits:
- Type enforcement
- Simpler queries
- No serialization needed
- Default values at database level
- Better indexing potential

### 2. Data Migration Plan
```python
def migrate_spawn_positions():
    """Migrate from JSON to individual columns"""
    with get_db() as db:
        # Get all NPCs with spawn positions
        npcs = db.execute("SELECT id, spawn_position FROM npcs").fetchall()
        
        for npc in npcs:
            try:
                # Parse existing JSON
                pos = json.loads(npc['spawn_position'] or '{"x":0,"y":5,"z":0}')
                
                # Update with individual columns
                db.execute("""
                    UPDATE npcs 
                    SET spawn_x = ?, spawn_y = ?, spawn_z = ?
                    WHERE id = ?
                """, (
                    float(pos.get('x', 0)),
                    float(pos.get('y', 5)),
                    float(pos.get('z', 0)),
                    npc['id']
                ))
            except json.JSONDecodeError:
                # Handle invalid JSON
                db.execute("""
                    UPDATE npcs 
                    SET spawn_x = 0, spawn_y = 5, spawn_z = 0
                    WHERE id = ?
                """, (npc['id'],))
        
        db.commit()
```

### 3. Updated API Implementation
```python
@router.post("/api/npcs")
async def create_npc(
    game_id: int = Form(...),
    spawn_x: float = Form(0),
    spawn_y: float = Form(5),
    spawn_z: float = Form(0),
    # ... other fields ...
):
    with get_db() as db:
        cursor.execute("""
            INSERT INTO npcs (
                game_id, spawn_x, spawn_y, spawn_z, ...
            ) VALUES (?, ?, ?, ?, ...)
        """, (game_id, spawn_x, spawn_y, spawn_z, ...))
```

### 4. Lua Export Adaptation
```python
def format_npc_as_lua(npc: dict) -> str:
    """Format NPC for Lua with Vector3"""
    return f"""
        spawnPosition = Vector3.new({npc['spawn_x']}, {npc['spawn_y']}, {npc['spawn_z']}),
    """
```

## Implementation Steps

1. Database Updates:
   - Add new columns with defaults
   - Create migration script
   - Run migration on existing data
   - Verify data integrity

2. Backend Changes:
   - Update API endpoints
   - Modify CRUD operations
   - Update Lua export
   - Add coordinate validation

3. Frontend Updates:
   - Update form handling
   - Modify display logic
   - Add coordinate validation
   - Improve error messages

4. Testing Requirements:
   - Verify migration success
   - Test CRUD operations
   - Validate Lua export
   - Check form population

## Success Criteria
1. Spawn positions correctly stored in database
2. Frontend displays correct coordinates
3. Edit form pre-populated with values
4. Lua export maintains Vector3 format
5. No data loss during migration

## Rollback Plan
1. Keep spawn_position column during migration
2. Maintain dual writing during testing
3. Verify data consistency before removal
4. Keep backup of JSON data