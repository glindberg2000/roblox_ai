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
    console.log('=== Tab Change ===', {
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
        // First load NPCs, then populate asset selector
        window.loadNPCs().then(() => {
            populateAssetSelector();
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

        // Update UI
        const npcList = document.getElementById('npcList');
        if (npcList) {
            npcList.innerHTML = ''; // Clear existing list
            if (data.npcs && data.npcs.length > 0) {
                data.npcs.forEach(npc => {
                    const npcCard = document.createElement('div');
                    npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
                    npcCard.innerHTML = `
                        <div class="aspect-w-16 aspect-h-9 mb-4">
                            <img src="${npc.imageUrl || ''}" 
                                 alt="${npc.displayName}" 
                                 class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                        </div>
                        <h3 class="font-bold text-lg truncate text-gray-100">${npc.displayName}</h3>
                        <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId}</p>
                        <p class="text-sm text-gray-400 mb-2">Model: ${npc.model || 'Default'}</p>
                        <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${npc.systemPrompt || 'No personality defined'}</p>
                        <div class="text-sm text-gray-400 mb-4">
                            <div>Response Radius: ${npc.responseRadius}m</div>
                            <div>Abilities: ${(npc.abilities || []).join(', ') || 'None'}</div>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="window.editNPC('${npc.npcId}')" 
                                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                                Edit
                            </button>
                            <button onclick="window.deleteNPC('${npc.npcId}')" 
                                    class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                                Delete
                            </button>
                        </div>
                    `;
                    npcList.appendChild(npcCard);
                });
            } else {
                npcList.innerHTML = '<p class="text-gray-400 text-center p-4">No NPCs found</p>';
            }
        }

        return data;
    } catch (error) {
        console.error('UNIQUE-ID: Error loading NPCs:', error);
        showNotification('Failed to load NPCs: ' + error.message, 'error');
        return [];
    }
};







