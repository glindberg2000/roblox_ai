import pytest
from app.database import get_db
from app.config import SQLITE_DB_PATH

@pytest.mark.asyncio
async def test_database_initialization():
    """Test database initialization"""
    with get_db() as db:
        # Check if tables exist
        result = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='items'
        """).fetchone()
        assert result is not None

@pytest.mark.asyncio
async def test_get_items():
    """Test getting items from database"""
    with get_db() as db:
        # Insert test data
        db.execute("""
            INSERT INTO items (item_id, name, description)
            VALUES (?, ?, ?)
        """, ('test1', 'Test Item', 'Test Description'))
        db.commit()
        
        # Test retrieval
        cursor = db.execute("SELECT * FROM items")
        items = cursor.fetchall()
        assert len(items) > 0
        assert items[0]['name'] == 'Test Item' 