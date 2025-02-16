// Add at the very top with timestamp
console.log('=== DASHBOARD-NEW-INDEX-2023-11-22-A Loading index.js ===');

// Imports with version check
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';
import { editNPC } from './npc.js';  // Import editNPC

console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Imports loaded:', {
    showNotification: typeof showNotification,
    debugLog: typeof debugLog,
    state: typeof state,
    loadGames: typeof loadGames,
    editNPC: typeof editNPC  // Verify editNPC is imported
});

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Dashboard initialization');
    await loadGames();
});

// Enhanced populateAssetSelector with unique logging
async function populateAssetSelector() {
    console.log('populateAssetSelector called', {
        currentGame: state.currentGame,
        currentTab: state.currentTab
    });

    if (!state.currentGame) {
        console.warn('No game selected, cannot populate asset selector');
        return;
    }

    try {
        // Fetch assets for the current game
        const url = `/api/assets?game_id=${state.currentGame.id}`;
        console.log('Fetching assets from:', url);

        const response = await fetch(url);
        const data = await response.json();
        console.log('Received assets:', data);

        // Find and populate the selector
        const assetSelect = document.getElementById('assetSelect');
        if (!assetSelect) {
            console.error('Asset select element not found in DOM');
            return;
        }

        // Clear and populate the selector
        assetSelect.innerHTML = '<option value="">Select a model...</option>';
        if (data.assets && Array.isArray(data.assets)) {
            data.assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.assetId || asset.asset_id;
                option.textContent = asset.name;
                assetSelect.appendChild(option);
            });
            console.log(`Added ${data.assets.length} options to asset selector`);
        }
    } catch (error) {
        console.error('Error populating asset selector:', error);
        throw error; // Propagate error for handling in switchTab
    }
}

// Enhanced tab management with unique logging
window.showTab = function (tabName) {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Tab Change:', {
        from: state.currentTab,
        to: tabName,
        gameId: state.currentGame?.id
    });

    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    const tabElement = document.getElementById(`${tabName}Tab`);
    tabElement.classList.remove('hidden');
    updateCurrentTab(tabName);

    // Load content based on tab
    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        // First load NPCs, then populate the asset selector
        window.loadNPCs().then(() => {
            window.populateAssetSelector();
            console.log('NPCs loaded and asset selector populated');
        }).catch(error => {
            console.error('Error loading NPCs:', error);
        });
    }
};

// Make functions globally available
window.populateAssetSelector = populateAssetSelector;
window.loadNPCs = async function () {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Loading NPCs');
    try {
        const response = await fetch(`/api/npcs?game_id=${state.currentGame.id}`);
        const data = await response.json();
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: NPCs loaded:', data);

        // Store NPCs in state
        state.currentNPCs = data.npcs;

        // Update UI
        const npcList = document.getElementById('npcList');
        if (npcList) {
            npcList.innerHTML = '';
            if (data.npcs && data.npcs.length > 0) {
                data.npcs.forEach(npc => {
                    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Creating NPC card:', npc);
                    const npcCard = document.createElement('div');
                    npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';

                    // Parse spawn position
                    let spawnPos;
                    try {
                        spawnPos = typeof npc.spawnPosition === 'string' ?
                            JSON.parse(npc.spawnPosition) :
                            npc.spawnPosition || { x: 0, y: 5, z: 0 };
                    } catch (e) {
                        console.error('Error parsing spawn position:', e);
                        spawnPos = { x: 0, y: 5, z: 0 };
                    }

                    // Format abilities with icons
                    const abilityIcons = (npc.abilities || []).map(abilityId => {
                        const ability = window.ABILITY_CONFIG.find(a => a.id === abilityId);
                        return ability ? `<i class="${ability.icon}" title="${ability.name}"></i>` : '';
                    }).join(' ');

                    npcCard.innerHTML = `
                        <div class="aspect-w-16 aspect-h-9 mb-4">
                            <img src="${npc.imageUrl || ''}" 
                                 alt="${npc.displayName}" 
                                 class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                        </div>
                        <h3 class="font-bold text-lg truncate text-gray-100">${npc.displayName}</h3>
                        <div class="flex justify-between items-center mb-2">
                            <p class="text-sm text-gray-400">Asset ID: ${npc.assetId}</p>
                            <label class="inline-flex items-center cursor-pointer">
                                <input type="checkbox" 
                                    class="form-checkbox h-5 w-5 text-blue-600 bg-dark-700 border-dark-600 rounded"
                                    onchange="toggleNPC(event, '${npc.npcId}')"
                                    ${npc.enabled ? 'checked' : ''}
                                >
                                <span class="ml-2 text-sm text-gray-400">Enabled</span>
                            </label>
                        </div>
                        <p class="text-sm text-gray-400 mb-2">Model: ${npc.model || 'Default'}</p>
                        <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${npc.systemPrompt || 'No personality defined'}</p>
                        <div class="text-sm text-gray-400 mb-4">
                            <div>Response Radius: ${npc.responseRadius}m</div>
                            <div class="grid grid-cols-3 gap-1 mb-2">
                                <div>X: ${spawnPos.x.toFixed(2)}</div>
                                <div>Y: ${spawnPos.y.toFixed(2)}</div>
                                <div>Z: ${spawnPos.z.toFixed(2)}</div>
                            </div>
                            <div class="text-xl space-x-2">${abilityIcons}</div>
                        </div>
                        <div class="flex space-x-2">
                            <button class="edit-npc-btn flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Edit
                            </button>
                            <button class="delete-npc-btn flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                                Delete
                            </button>
                        </div>
                    `;

                    // Add event listeners
                    const editBtn = npcCard.querySelector('.edit-npc-btn');
                    const deleteBtn = npcCard.querySelector('.delete-npc-btn');

                    editBtn.addEventListener('click', () => {
                        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Edit clicked for NPC:', npc.npcId);
                        window.editNPC = editNPC;
                        editNPC(npc.npcId);
                    });

                    deleteBtn.addEventListener('click', async () => {
                        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Delete clicked for NPC:', npc.npcId);
                        if (confirm(`Are you sure you want to delete NPC "${npc.displayName}"?`)) {
                            try {
                                const response = await fetch(`/api/npcs/${npc.npcId}?game_id=${state.currentGame.id}`, {
                                    method: 'DELETE'
                                });

                                if (!response.ok) {
                                    const error = await response.json();
                                    throw new Error(error.detail || 'Failed to delete NPC');
                                }

                                showNotification('NPC deleted successfully', 'success');
                                loadNPCs();  // Refresh the list
                            } catch (error) {
                                console.error('Error deleting NPC:', error);
                                showNotification(error.message, 'error');
                            }
                        }
                    });

                    npcList.appendChild(npcCard);
                });
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
};

// Add this to verify the function is available
console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Checking global functions:', {
    editNPC: typeof window.editNPC,
    deleteNPC: typeof window.deleteNPC,
    loadNPCs: typeof window.loadNPCs
});

// Tab switching function
function switchTab(tabName) {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Switching to tab:', tabName, {
        currentGame: state.currentGame,
        currentTab: state.currentTab
    });

    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}Tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }

    // Update state
    state.currentSection = tabName;
    updateCurrentTab(tabName);

    // Load content based on the tab
    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        console.log('Loading NPCs tab content...');

        // First load NPCs
        window.loadNPCs()
            .then(() => {
                console.log('NPCs loaded, populating asset selector...');
                // Then populate the asset selector with NPC assets only
                return window.populateCreateFormAssets();
            })
            .catch(error => {
                console.error('Error in NPC tab initialization:', error);
                showNotification('Error loading NPC data', 'error');
            });
    }
}

// Initialize navigation
document.addEventListener('DOMContentLoaded', () => {
    // Set up navigation click handlers
    const navButtons = {
        'nav-games': 'games',
        'nav-assets': 'assets',
        'nav-npcs': 'npcs',
        'nav-players': 'players'
    };

    Object.entries(navButtons).forEach(([buttonId, tabName]) => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', () => {
                if (!button.disabled || tabName === 'games') {
                    switchTab(tabName);
                }
            });
        }
    });

    // Start with games tab
    switchTab('games');
});

// Make functions globally available
window.switchTab = switchTab;
window.populateAssetSelector = populateAssetSelector;

// Export for module use
export { switchTab };







