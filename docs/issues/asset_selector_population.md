Asset Selector Population Issue

Problem Description:
-------------------
The NPC creation form's asset selector is not being populated with available assets, despite:
1. The API correctly returning assets (logs show "Found 1 assets")
2. The game state being correctly loaded
3. The populateAssetSelector function being called

Server Logs:
-----------
Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,612 - roblox_app - INFO - Game: 666 (ID: 59, Assets: 12, NPCs: 9)
Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,613 - roblox_app - INFO - Game: Game 1 (ID: 3, Assets: 11, NPCs: 6)
Nov 20 04:26:13 ubuntu22 fastapi-roblox[646396]: 2024-11-20 04:26:13,613 - roblox_app - INFO - Game: Sandbox V1 (ID: 61, Assets: 1, NPCs: 0)
Nov 20 04:26:16,485 - roblox_app - INFO - Fetching assets for game_id: 61, type: NPC
Nov 20 04:26:16,486 - roblox_app - INFO - Found 1 assets

Current Implementation:
---------------------
1. Frontend JavaScript (index.js):
```javascript
async function populateAssetSelector() {
    console.log('Current game state:', state.currentGame);
    if (!state.currentGame) {
        console.log('No game selected for asset selector');
        return;
    }

    try {
        console.log('Fetching assets for game:', state.currentGame.id);
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        console.log('Received assets:', data);
        
        const assetSelect = document.getElementById('assetSelect');
        console.log('Asset select element:', assetSelect);
        if (assetSelect) {
            assetSelect.innerHTML = '<option value="">Select a model...</option>';
            
            if (data.assets && Array.isArray(data.assets)) {
                data.assets.forEach(asset => {
                    const option = document.createElement('option');
                    option.value = asset.assetId;
                    option.textContent = asset.name;
                    assetSelect.appendChild(option);
                    console.log('Added option:', asset.name);
                });
            }
        }
    } catch (error) {
        console.error('Error loading models for selector:', error);
    }
}
```

2. HTML Form Structure:
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

3. State Management:
```javascript
export const state = {
    currentGame: null,
    currentTab: 'games'
};

export function updateCurrentGame(game) {
    state.currentGame = game;
}
```

API Response Structure:
---------------------
{
    "assets": [
        {
            "id": "123",
            "assetId": "14768974964",
            "name": "Asset Name",
            "description": "Asset Description",
            "type": "NPC",
            "imageUrl": "https://example.com/image.png"
        }
    ]
}

Current Behavior:
---------------
1. Server logs show assets are being fetched successfully
2. API returns correct data structure
3. populateAssetSelector function is being called
4. Select element is not being populated

Diagnostic Steps:
---------------
1. Frontend Console Logging:
   - Add logging for state updates
   - Track DOM content loaded events
   - Monitor asset loading process

2. DOM Element Verification:
   - Element existence
   - Element visibility
   - Parent container visibility
   - Tab state when selector is populated

3. State Management Verification:
   - Verify state.currentGame is set when game is selected
   - Check timing of state updates vs DOM updates
   - Verify state persistence between tab switches

4. API Response Verification:
   - Check network tab for response format
   - Verify asset data structure matches expectations
   - Check for any error responses

Questions to Answer:
------------------
1. Is the select element present in the DOM when populateAssetSelector runs?
2. Is state.currentGame populated with correct game data?
3. Is the function being called at the right time in the page lifecycle?
4. Are there any JavaScript errors in the console?
5. Is the tab visibility affecting the element accessibility?

Expected Behavior:
----------------
1. When a game is selected, state.currentGame should be updated
2. When the NPC tab is shown, populateAssetSelector should run
3. The select element should be populated with available assets
4. Users should see a list of assets to choose from

Next Steps:
----------
1. Add all suggested console logs
2. Check browser console for any errors
3. Verify the API response structure
4. Check the timing of state updates vs DOM updates
5. Verify the select element is accessible when populateAssetSelector runs
6. Add DOM mutation observer to track element changes
7. Add tab visibility state logging

