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