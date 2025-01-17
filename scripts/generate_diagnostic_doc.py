import os
from pathlib import Path

def generate_diagnostic_doc():
    # Create docs/issues directory if it doesn't exist
    doc_path = Path(__file__).parent.parent / "docs" / "issues"
    doc_path.mkdir(parents=True, exist_ok=True)
    
    # Server logs from the issue
    server_logs = """Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,612 - roblox_app - INFO - Game: 666 (ID: 59, Assets: 12, NPCs: 9)
Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,613 - roblox_app - INFO - Game: Game 1 (ID: 3, Assets: 11, NPCs: 6)
Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,613 - roblox_app - INFO - Game: Sandbox V1 (ID: 61, Assets: 1, NPCs: 0)
Nov 20 04:26:16,485 - roblox_app - INFO - Fetching assets for game_id: 61, type: NPC
Nov 20 04:26:16,486 - roblox_app - INFO - Found 1 assets"""
    
    # Read relevant code files
    index_js_path = Path(__file__).parent.parent / "api" / "static" / "js" / "dashboard_new" / "index.js"
    with open(index_js_path, 'r') as f:
        index_js = f.read()
    
    # Generate the markdown content
    content = f"""# Asset Selector Population Issue

## Problem Description
The NPC creation form's asset selector is not being populated with available assets, despite:
1. The API correctly returning assets (logs show "Found 1 assets")
2. The game state being correctly loaded
3. The populateAssetSelector function being called

## Server Logs
{server_logs}

## Current Implementation

### 1. Frontend JavaScript (index.js)
```javascript
{index_js}
```

### 2. HTML Form Structure
```html
<form id="npcForm" onsubmit="createNPC(event)" class="space-y-4">
    <div>
        <label class="block text-sm font-medium mb-1 text-gray-300">Asset:</label>
        <select name="assetID" required 
            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
            id="assetSelect">
            <option value="">Select an asset...</option>
        </select>
    </div>
</form>
```

### 3. State Management
```javascript
// state 