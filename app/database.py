import sqlite3
from contextlib import contextmanager
import json

@contextmanager
def get_db():
    db = sqlite3.connect('./db/game_data.db')
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def get_items(game_id=None):
    with get_db() as db:
        cursor = db.cursor()
        if game_id:
            cursor.execute('SELECT * FROM items WHERE game_id = ?', (game_id,))
        else:
            cursor.execute('SELECT * FROM items')
        return [dict(row) for row in cursor.fetchall()]

def export_to_lua(game_id=None):
    items = get_items(game_id)
    # Your existing Lua conversion logic here
    return lua_content 