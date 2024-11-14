import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import DB_DIR, SQLITE_DB_PATH

@contextmanager
def get_db():
    db = sqlite3.connect(SQLITE_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db() as db:
        # Create schema
        schema_path = DB_DIR / 'schema.sql'
        with open(schema_path, 'r') as f:
            db.executescript(f.read())
        
        # Execute migrations
        migrations_dir = DB_DIR / 'migrations'
        if migrations_dir.exists():
            for file in sorted(migrations_dir.glob('*.sql')):
                with open(file, 'r') as f:
                    db.executescript(f.read())

def get_items(game_id=None):
    with get_db() as db:
        cursor = db.cursor()
        if game_id:
            cursor.execute('SELECT * FROM items WHERE game_id = ?', (game_id,))
        else:
            cursor.execute('SELECT * FROM items')
        return [dict(row) for row in cursor.fetchall()]
