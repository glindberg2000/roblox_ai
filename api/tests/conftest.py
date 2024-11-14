import pytest
import os
import sys
from pathlib import Path
from httpx import AsyncClient
from httpx import ASGITransport

# Add api directory to Python path
api_path = Path(__file__).parent.parent
sys.path.append(str(api_path))

from app.main import app
from app.database import init_db, get_db

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
    print("Initializing test database...")
    init_db()  # Initialize database with schema
    yield
    print("Cleaning up test database...")
    # Cleanup after test
    with get_db() as db:
        db.execute("DELETE FROM items")
        db.commit()

@pytest.fixture
async def client():
    """Create a test client"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client 