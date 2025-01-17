# NPC Edit Modal Not Launching - Field Name and Type Mismatch

## Problem Description
The NPC edit modal fails to launch with a "NPC Not Found" error due to:
1. Field name mismatch between code and data (`npcId` vs `id`)
2. Potential data type mismatch (string vs number)

## Current State
1. Backend returns NPC data with `id` field:
```javascript
// Backend response
{
    "id": npc["id"],
    "npcId": npc["npc_id"],
    "displayName": npc["display_name"],
    // ...
}
```

2. Frontend tries to find NPC using wrong field:
```javascript
// Current code - fails
const npc = currentNPCs.find(n => n.npcId === npcId);
```

## Root Cause Analysis

1. Field Name Mismatch:
```javascript
// In loadNPCs()
currentNPCs = data.npcs;  // NPCs have 'id' field

// In editNPC()
const npc = currentNPCs.find(n => n.npcId === npcId);  // Looking for 'npcId' field
```

2. Data Type Mismatch:
```javascript
// Button click passes string
<button onclick="editNPC('${npc.id}')">  // String due to template literal

// Comparison uses strict equality
n.npcId === npcId  // '1' === 1 is false
```

## Data Flow Analysis

1. Backend Route:
```python
@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str, game_id: int):
    # ... database query ...
    npc_data = {
        "id": npc["id"],          # Number from database
        "npcId": npc["npc_id"],   # String UUID
        # ...
    }
```

2. Frontend Storage:
```javascript
fetch(`/api/npcs?game_id=${currentGame.id}`)
    .then(response => response.json())
    .then(data => {
        currentNPCs = data.npcs;  // Stores array of NPCs
        // Each NPC has both 'id' and 'npcId' fields
    });
```

## Proposed Fix

1. Update NPC Lookup:
```javascript
function editNPC(npcId) {
    debugLog('Editing NPC', { npcId, type: typeof npcId });
    try {
        // Log available NPCs
        debugLog('Available NPCs', currentNPCs.map(n => ({
            id: n.id,
            npcId: n.npcId,
            types: {
                id: typeof n.id,
                npcId: typeof n.npcId
            }
        })));
        
        // Use npcId field and ensure string comparison
        const npc = currentNPCs.find(n => String(n.npcId) === String(npcId));
        
        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }
        
        debugLog('Found NPC', npc);
        
        // Populate form fields
        document.getElementById('editNpcId').value = npc.npcId;  // Use npcId consistently
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcModel').value = npc.assetId;
        document.getElementById('editNpcRadius').value = npc.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npc.systemPrompt || '';

        // Show modal
        const modal = document.getElementById('npcEditModal');
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error opening NPC edit modal:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}
```

2. Update Button Generation:
```javascript
currentNPCs.forEach(npc => {
    const npcCard = document.createElement('div');
    npcCard.innerHTML = `
        <!-- ... other HTML ... -->
        <button onclick="editNPC('${npc.npcId}')"  // Use npcId consistently
                class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Edit
        </button>
    `;
});
```

## Verification Steps

1. Add Debug Logging:
```javascript
// At the start of loadNPCs
debugLog('Loading NPCs', {
    gameId: currentGame.id,
    gameSlug: currentGame.slug
});

// After fetching NPCs
debugLog('Loaded NPCs', currentNPCs.map(n => ({
    id: n.id,
    npcId: n.npcId,
    displayName: n.displayName
})));
```

2. Test Cases:
- Load NPCs and verify data structure
- Click edit button and check passed ID
- Verify modal opens with correct data
- Test with different NPC types

## Implementation Plan

1. Update Field Usage:
- Use `npcId` consistently throughout the code
- Convert IDs to strings for comparison
- Add type checking and validation

2. Add Error Handling:
- Validate NPC data structure
- Add detailed error messages
- Log data state at each step

3. Improve Modal Management:
- Add loading states
- Handle modal errors gracefully
- Add validation before showing

## Next Steps
1. Implement field name standardization
2. Add data type validation
3. Update error handling
4. Add comprehensive logging
5. Test with various NPC types