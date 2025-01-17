# NPC Edit Modal Not Launching - Module Import Issue

## Problem Description
The NPC edit modal fails to launch after clicking the edit button. The console shows the click is registered but the modal doesn't appear.

## Current State

1. Console logs show successful initialization:
```javascript
=== DASHBOARD-NEW-INDEX-2023-11-22-A Loading index.js ===
DASHBOARD-NEW-INDEX-2023-11-22-A: Imports loaded: {
    showNotification: 'function',
    debugLog: 'function',
    state: 'object',
    loadGames: 'function',
    editNPC: 'function'
}
```

2. NPCs are loaded and edit button click is detected:
```javascript
DASHBOARD-NEW-INDEX-2023-11-22-A: Edit clicked for NPC: b11fbfb5-5f46-40cb-9c4c-84ca72b55ac7
```

## Code Analysis

1. Module Import Structure:
```javascript
// index.js
import { editNPC } from './npc.js';  // Importing from npc.js module

// Event listener setup
editBtn.addEventListener('click', () => {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Edit clicked for NPC:', npc.npcId);
    editNPC(npc.npcId);  // Using imported function
});
```

2. Modal Management:
```javascript
// ui.js
export function showModal(content) {
    console.log('Showing modal with content:', content);
    
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    // ... modal creation code ...
}

// Making it globally available
window.showModal = showModal;
```

3. NPC Edit Function:
```javascript
// npc.js
export async function editNPC(npcId) {
    try {
        console.log('Editing NPC:', npcId);
        
        if (!state.currentGame) {
            showNotification('Please select a game first', 'error');
            return;
        }

        // Find NPC using npcId
        const npc = state.currentNPCs.find(n => n.npcId === npcId);
        // ... modal creation and display code ...
        window.showModal(modalContent);  // Using global showModal
    } catch (error) {
        console.error('Error editing NPC:', error);
        showNotification('Failed to edit NPC: ' + error.message, 'error');
    }
}
```

## Root Cause Analysis

1. Module Import Chain:
- index.js imports editNPC from npc.js
- npc.js uses showModal from ui.js
- ui.js exports showModal and adds it to window
- Potential timing issue with global function availability

2. Function Availability:
- editNPC is imported as module function
- showModal is expected to be global
- Possible race condition between module loading and global registration

3. State Management:
- state.currentNPCs must be populated
- state.currentGame must be set
- Both managed by state.js module

## Debugging Steps

1. Add Function Availability Checks:
```javascript
// In npc.js editNPC function
console.log('Function availability:', {
    showModal: typeof window.showModal,
    state: typeof state,
    currentGame: state?.currentGame,
    currentNPCs: state?.currentNPCs?.length
});
```

2. Add Modal Creation Logging:
```javascript
// In ui.js showModal function
console.log('Modal creation:', {
    content: content,
    backdrop: backdrop,
    modal: modal
});
```

3. Add State Verification:
```javascript
// In npc.js before NPC lookup
console.log('State check:', {
    currentNPCs: state.currentNPCs,
    foundNPC: state.currentNPCs.find(n => n.npcId === npcId)
});
```

## Proposed Solutions

1. Use Module-Only Approach:
```javascript
// ui.js
export function showModal(content) { ... }

// npc.js
import { showModal } from './ui.js';
export async function editNPC(npcId) { ... }
```

2. Ensure Global Registration:
```javascript
// ui.js
export function showModal(content) { ... }
window.showModal = showModal;

// Verify registration
console.log('Modal function registered:', {
    showModal: typeof window.showModal,
    source: window.showModal.toString().slice(0, 50)
});
```

3. Add Error Boundaries:
```javascript
// npc.js
export async function editNPC(npcId) {
    try {
        if (typeof window.showModal !== 'function') {
            throw new Error('Modal function not available');
        }
        // ... rest of function
    } catch (error) {
        console.error('EditNPC Error:', error);
        showNotification(error.message, 'error');
    }
}
```

## Next Steps

1. Implement Function Checks:
- Add availability logging
- Add error boundaries
- Verify module loading order

2. Add State Validation:
- Verify currentNPCs data
- Check state management
- Add state loading indicators

3. Improve Error Handling:
- Add specific error messages
- Implement fallback behavior
- Add user feedback

4. Update Module Structure:
- Review import/export pattern
- Consider bundling approach
- Add module loading checks 