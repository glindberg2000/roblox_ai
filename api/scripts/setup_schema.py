#!/usr/bin/env python3

import os
import sys
from pathlib import Path
import sqlite3
from api.app.config import SQLITE_DB_PATH, ensure_game_directories
from api.app.database import init_db

def setup_database():
    """Initialize the database and create required directories"""
    # Initialize database
    init_db()
    
    # Ensure default game directories exist
    ensure_game_directories("game1")
    
    print("Database and directories initialized successfully")

if __name__ == "__main__":
    setup_database() 