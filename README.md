## Location API Documentation

The Location API provides endpoints for managing and querying location-based assets in the game.

### Endpoints

#### List Locations
```http
GET /api/locations?game_id={game_id}&area={area}
```
Lists all location assets, optionally filtered by game and area.

#### Get Single Asset
```http
GET /api/assets/{asset_id}?game_id={game_id}
```
Get detailed information about a specific asset.

#### Search Locations
```http
GET /api/locations/search?game_id={game_id}&x={x}&y={y}&z={z}&radius={radius}&area={area}
```
Search for locations near a point in 3D space.

### Example Usage

```python
import requests

# List all locations in spawn area
response = requests.get(
    "http://localhost:8000/api/locations",
    params={"game_id": 61, "area": "spawn_area"}
)
locations = response.json()

# Search for locations near a point
response = requests.get(
    "http://localhost:8000/api/locations/search",
    params={
        "game_id": 61,
        "x": 5,
        "y": 3,
        "z": 3,
        "radius": 10
    }
)
nearby = response.json()

# Get single asset details
response = requests.get(
    "http://localhost:8000/api/assets/96144138651755",
    params={"game_id": 61}
)
asset = response.json()
```

### Response Format

Locations are returned in the following format:
```json
{
    "asset_id": "96144138651755",
    "name": "Pete's Merch Stand",
    "type": "Prop",
    "is_location": true,
    "position_x": -10.289,
    "position_y": 21.512,
    "position_z": -127.797,
    "location_data": {
        "area": "spawn_area",
        "type": "shop",
        "owner": "Pete",
        "interactable": true,
        "tags": ["shop", "retail"]
    },
    "aliases": ["stand", "merchant stand"]
}
``` 