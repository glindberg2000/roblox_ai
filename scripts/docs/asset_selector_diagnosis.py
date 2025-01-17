"""Asset Selector Population Issue - Diagnosis and Solution

Problem Overview:
----------------
The asset selector in the NPC tab is not being populated despite:
- API returning correct data
- populateAssetSelector function being called
- state.currentGame being set

Root Cause Analysis:
------------------
Primary issue appears to be timing-related:
1. assetSelect element may not exist in DOM when function runs
2. Function might execute before tab content is rendered
3. State updates may not be synchronized with DOM updates

Diagnostic Steps:
---------------
1. DOM Element Verification:
```javascript
// Add to populateAssetSelector()
console.log('DOM ready state:', document.readyState);
console.log('Asset select element:', assetSelect);
console.log('Parent tab visibility:', 
    document.getElementById('npcsTab')?.classList.contains('hidden'));
```

2. State Management Check:
```javascript
// Add to updateCurrentGame()
export function updateCurrentGame(game) {
    console.log('Updating game state:', game);
    state.currentGame = game;
    console.log('New state:', state);
}
```

3. Tab Activation Monitoring:
```javascript
// Add to showTab()
window.showTab = function(tabName) {
    console.log('Showing tab:', tabName);
    console.log('Previous tab:', state.currentTab);
    // ... existing code ...
}
```

4. Asset Loading Verification:
```javascript
// Add to populateAssetSelector()
try {
    console.log('Fetching assets for game:', state.currentGame.id);
    const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
    const data = await response.json();
    console.log('Asset response:', data);
    // ... existing code ...
}
```

Recommended Solution:
-------------------
1. Move populateAssetSelector call to tab activation:
```javascript
window.showTab = function(tabName) {
    console.log('Showing tab:', tabName);
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    updateCurrentTab(tabName);

    if (tabName === 'npcs' && state.currentGame) {
        // Ensure tab is visible before populating
        setTimeout(() => {
            populateAssetSelector();
        }, 0);
    }
};
```

2. Add DOM Content Verification:
```javascript
async function populateAssetSelector() {
    if (document.readyState !== 'complete') {
        console.warn('DOM not fully loaded, deferring selector population');
        return;
    }
    
    const npcsTab = document.getElementById('npcsTab');
    if (npcsTab?.classList.contains('hidden')) {
        console.warn('NPCs tab is hidden, deferring selector population');
        return;
    }
    
    // ... rest of function
}
```

3. Add MutationObserver for DOM Changes:
```javascript
const observeDOM = () => {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && 
                document.getElementById('assetSelect')) {
                console.log('Asset select element added to DOM');
                observer.disconnect();
                populateAssetSelector();
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
};
```

Implementation Steps:
------------------
1. Add console logging as shown above
2. Modify tab activation logic
3. Add DOM content verification
4. Implement MutationObserver if needed
5. Test with browser dev tools open
6. Verify timing of state updates vs DOM updates

Expected Results:
---------------
1. Console should show clear sequence of:
   - DOM ready state
   - Tab activation
   - Element existence
   - Asset loading
   - Selector population

2. Asset selector should populate when:
   - DOM is fully loaded
   - NPC tab is visible
   - state.currentGame is set
   - assetSelect element exists

Verification Steps:
-----------------
1. Check browser console for:
   - Element existence logs
   - State update logs
   - API response logs
   - Any error messages

2. Verify in Network tab:
   - API calls timing
   - Response structure
   - Request parameters

3. Confirm in Elements tab:
   - assetSelect element exists
   - Tab visibility state
   - DOM structure integrity
"""

def get_diagnosis():
    """Return the diagnosis documentation as a string."""
    return __doc__

if __name__ == "__main__":
    print(get_diagnosis()) 