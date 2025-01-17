import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    """Test creating a new item via API"""
    # Use multipart/form-data format
    files = {
        'assetId': (None, 'test123'),
        'name': (None, 'Test Asset'),
        'description': (None, 'Test Description'),
        'storage_type': (None, 'npcs')
    }
    
    response = await client.post(
        "/api/assets",
        files=files  # Use files parameter for form data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Asset"
    assert data["assetId"] == "test123" 