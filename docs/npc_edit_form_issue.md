# NPC Edit Form Population Issue

## Problem Description
The NPC edit form modal is not properly populating form fields with existing NPC data, even though the data is correctly fetched from the server.

## Current State
1. NPC data is successfully fetched and logged:
```javascript
NPC data to edit: {
    id: 126,
    npcId: '843fb9ff-c5e1-4c22-9378-cb6ddabbc41a',
    displayName: 'Officer Egg',
    assetId: '4613203451',
    assetName: 'Police Officer'
}
```

2. Form fields are empty after render:
```javascript
Form values after render: {
    displayName: '',
    model: '',
    radius: '',
    prompt: ''
}
```

3. Form submission contains empty values:
```javascript
Form data before validation: {
    displayName: '',
    assetId: '',
    responseRadius: NaN,
    systemPrompt: '',
    abilities: Array(1)
}
```

## Console Logs
```
index.js:39 Populated asset selector with 3 assets
npc.js:95 NPC data to edit: {id: 126, npcId: '843fb9ff-c5e1-4c22-9378-cb6ddabbc41a', displayName: 'Officer Egg', assetId: '4613203451', assetName: 'Police Officer', …}
npc.js:177 Form values after render: {displayName: '', model: '', radius: '', prompt: ''}
npc.js:198 Form data before validation: {displayName: '', assetId: '', responseRadius: NaN, systemPrompt: '', abilities: Array(1)}
```

## Key Files and Components
1. Frontend:
   - NPC edit form implementation (npc.js)
   - State management (state.js)
   - Modal handling (ui.js)
2. Backend:
   - NPC update endpoint (dashboard_router.py)
   - Database operations
   - Error handling

## Required Files for Analysis
1. api/static/js/dashboard_new/npc.js
2. api/static/js/dashboard_new/state.js
3. api/static/js/dashboard_new/ui.js
4. api/app/dashboard_router.py 