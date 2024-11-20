// Immediate execution check - add at very top
console.log('UNIQUE-ID: Loading index.js version:', '2023-11-20-J');

// Imports
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';

// Verify imports loaded
console.log('UNIQUE-ID: Imports loaded:', {
    showNotification: typeof showNotification,
    debugLog: typeof debugLog,
    state: typeof state,
    loadGames: typeof loadGames
});

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('UNIQUE-ID: Dashboard initialization');
    await loadGames();
});

// Enhanced populateAssetSelector with immediate logging
async function populateAssetSelector() {
    console.log('UNIQUE-ID: Asset selector population start');
    console.log('UNIQUE-ID: Current game:', state.currentGame);

    // Immediate DOM check
    const assetSelect = document.getElementById('assetSelect');
    console.log('UNIQUE-ID: Asset select element:', {
        exists: !!assetSelect,
        id: assetSelect?.id,
        parent: assetSelect?.parentElement?.id
    });

    if (!state.currentGame) {
        console.log('UNIQUE-ID: No game selected, aborting');
        return;
    }

    try {
        // 1. Fetch assets
        const url = `/api/assets?game_id=${state.currentGame.id}&type=NPC`;
        console.log('UNIQUE-ID: Fetching from:', url);
        
        const response = await fetch(url);
        const text = await response.text();
        console.log('UNIQUE-ID: Raw response:', text);
        
        const data = JSON.parse(text);
        console.log('UNIQUE-ID: Parsed response:', data);

        // 2. Verify select element again
        if (!assetSelect) {
            console.log('UNIQUE-ID: Asset select still not found after fetch');
            return;
        }

        // 3. Clear and populate
        assetSelect.innerHTML = '<option value="">Select a model...</option>';
        console.log('UNIQUE-ID: Cleared select options');

        let added = 0;
        if (data.assets && Array.isArray(data.assets)) {
            data.assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.assetId || asset.asset_id;
                option.textContent = asset.name;
                assetSelect.appendChild(option);
                added++;
                console.log('UNIQUE-ID: Added option:', {value: option.value, text: option.textContent});
            });
        }

        console.log('UNIQUE-ID: Final select state:', {
            optionsAdded: added,
            totalOptions: assetSelect.options.length,
            currentValue: assetSelect.value,
            innerHTML: assetSelect.innerHTML
        });

    } catch (error) {
        console.error('UNIQUE-ID: Error in populateAssetSelector:', error);
    }
}

// Enhanced tab management
window.showTab = function(tabName) {
    console.log('UNIQUE-ID: Tab change:', {
        from: state.currentTab,
        to: tabName,
        gameId: state.currentGame?.id
    });

    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    const tabElement = document.getElementById(`${tabName}Tab`);
    tabElement.classList.remove('hidden');
    updateCurrentTab(tabName);

    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        // Load NPCs then assets
        requestAnimationFrame(async () => {
            try {
                console.log('UNIQUE-ID: NPC tab initialization');
                const npcs = await window.loadNPCs();
                console.log('UNIQUE-ID: NPCs loaded:', npcs);
                await populateAssetSelector();
            } catch (error) {
                console.error('UNIQUE-ID: Error in NPC tab:', error);
            }
        });
    }
};

// Make functions globally available
window.populateAssetSelector = populateAssetSelector;
window.loadNPCs = async function() {
    console.log('UNIQUE-ID: Loading NPCs');
    try {
        const response = await fetch(`/api/npcs?game_id=${state.currentGame.id}`);
        const data = await response.json();
        console.log('UNIQUE-ID: NPCs loaded:', data);
        return data;
    } catch (error) {
        console.error('UNIQUE-ID: Error loading NPCs:', error);
        showNotification('Failed to load NPCs: ' + error.message, 'error');
        return [];
    }
};







