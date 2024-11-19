import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';

console.log('Loading NEW dashboard version');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing dashboard...');
    await loadGames();
});

// Add populateAssetSelector function
async function populateAssetSelector() {
    if (!state.currentGame) {
        console.log('No game selected for asset selector');
        return;
    }

    try {
        // Fetch only NPC type assets
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        
        const assetSelect = document.getElementById('editNpcModel');
        if (assetSelect) {
            // Clear existing options
            assetSelect.innerHTML = '<option value="">Select a model...</option>';
            
            // Add options for each asset
            if (data.assets && Array.isArray(data.assets)) {
                data.assets.forEach(asset => {
                    const option = document.createElement('option');
                    option.value = asset.assetId;
                    option.textContent = asset.name;
                    assetSelect.appendChild(option);
                });
            }
            console.log('Populated model selector with', data.assets?.length || 0, 'assets');
        }
    } catch (error) {
        console.error('Error loading models for selector:', error);
        showNotification('Failed to load models for selection', 'error');
    }
}

// Tab management
window.showTab = function(tabName) {
    console.log('Showing tab:', tabName);
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    updateCurrentTab(tabName);

    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        window.loadNPCs();
        populateAssetSelector();
    }
};

// Make populateAssetSelector globally available
window.populateAssetSelector = populateAssetSelector;







