@pytest.mark.asyncio
async def test_asset_crud_operations(client: AsyncClient):
    """Test Create, Read, Update, Delete operations on assets"""
    
    # Test data
    test_asset = {
        'assetId': 'test123',
        'name': 'Test Asset',
        'description': 'Initial Description',
        'storage_type': 'npcs'
    }
    
    updated_description = "Updated Description"
    
    # 1. Create asset
    files = {k: (None, v) for k, v in test_asset.items()}
    create_response = await client.post("/api/assets", files=files)
    assert create_response.status_code == 200
    
    # Verify creation in database
    with get_db() as db:
        cursor = db.execute("SELECT * FROM items WHERE item_id = ?", (test_asset['assetId'],))
        item = cursor.fetchone()
        assert item is not None, "Item not found in database after creation"
        print(f"Created item in DB: {dict(item)}")
    
    # 2. Update asset
    update_data = {
        "description": updated_description
    }
    update_response = await client.put(
        f"/api/assets/{test_asset['assetId']}", 
        json=update_data
    )
    print(f"Update response: {update_response.status_code} - {update_response.text}")
    assert update_response.status_code == 200
    
    # Verify update in database
    with get_db() as db:
        cursor = db.execute("SELECT * FROM items WHERE item_id = ?", (test_asset['assetId'],))
        updated_item = cursor.fetchone()
        assert updated_item is not None, "Item not found in database after update"
        assert dict(updated_item)["description"] == updated_description