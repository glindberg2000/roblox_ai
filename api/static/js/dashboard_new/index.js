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
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Asset selector population start');
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Current game:', state.currentGame);

    // Immediate DOM check
    const assetSelect = document.getElementById('assetSelect');
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Asset select element:', {
        exists: !!assetSelect,
        id: assetSelect?.id,
        parent: assetSelect?.parentElement?.id
    });

    if (!state.currentGame) {
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: No game selected, aborting');
        return;
    }

    try {
        // 1. Fetch assets
        const url = `/api/assets?game_id=${state.currentGame.id}&type=NPC`;
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Fetching from:', url);
        
        const response = await fetch(url);
        const text = await response.text();
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Raw response:', text);
        
        const data = JSON.parse(text);
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Parsed response:', data);

        // 2. Verify select element again
        if (!assetSelect) {
            console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Asset select still not found after fetch');
            return;
        }

        // 3. Clear and populate
        assetSelect.innerHTML = '<option value="">Select a model...</option>';
        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Cleared select options');

        let added = 0;
        if (data.assets && Array.isArray(data.assets)) {
            data.assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.assetId || asset.asset_id;
                option.textContent = asset.name;
                assetSelect.appendChild(option);
                added++;
                console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Added option:', {value: option.value, text: option.textContent});
            });
        }

        console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Final select state:', {
            optionsAdded: added,
            totalOptions: assetSelect.options.length,
            currentValue: assetSelect.value,
            innerHTML: assetSelect.innerHTML
        });

    } catch (error) {
        console.error('DASHBOARD-NEW-INDEX-2023-11-22-A: Error in populateAssetSelector:', error);
    }
}

// Enhanced tab management with unique logging
window.showTab = function(tabName) {
    console.log('DASHBOARD-NEW-INDEX-2023-11-22-A: Tab Change', {
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
        window.loadNPCs().then(() => {
            populateAssetSelector();
        });
    }
};

// Make functions globally available
window.populateAssetSelector = populateAssetSelector;
window.loadNPCs = async function() {
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
                        <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId}</p>
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







