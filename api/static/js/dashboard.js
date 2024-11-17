// Dashboard state
let currentTab = 'games';  // Default to games tab
let currentGame = null;
let currentAssets = [];  // Store loaded assets
let currentNPCs = [];    // Store loaded NPCs

// Debug logging
console.log('Dashboard.js loaded');

// Initial state and utilities
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing dashboard');
    showTab('games');  // Start on games tab
    loadGames();
});

// Show/hide tabs
window.showTab = function(tabName) {  // Make showTab globally available
    console.log('Showing tab:', tabName);
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    currentTab = tabName;
    
    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && currentGame) {
        loadAssets();
    } else if (tabName === 'npcs' && currentGame) {
        loadNPCs();
        populateAssetSelector();
    }
}

// Update loadGames function with SELECT button
async function loadGames() {
    console.log('Loading games...');
    try {
        const response = await fetch('/api/games');
        const games = await response.json();
        console.log('Loaded games:', games);
        
        const gamesContainer = document.getElementById('games-container');
        if (!gamesContainer) {
            console.error('games-container element not found!');
            return;
        }
        
        gamesContainer.innerHTML = '';
        
        games.forEach(game => {
            console.log('Creating card for game:', game);
            const gameCard = document.createElement('div');
            gameCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            gameCard.innerHTML = `
                <h3 class="text-xl font-bold text-gray-100 mb-2">${game.title}</h3>
                <p class="text-gray-400 mb-4">${game.description || 'No description'}</p>
                <div class="flex items-center text-sm text-gray-400 mb-4">
                    <span class="mr-4"><i class="fas fa-cube"></i> Assets: ${game.asset_count || 0}</span>
                    <span><i class="fas fa-user"></i> NPCs: ${game.npc_count || 0}</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="selectGame('${game.slug}')" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200">
                        <i class="fas fa-check-circle"></i> Select
                    </button>
                    <button onclick="editGame('${game.slug}')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="deleteGame('${game.slug}')" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `;
            gamesContainer.appendChild(gameCard);
            console.log('Added game card:', game.title);
        });
    } catch (error) {
        console.error('Error loading games:', error);
        showNotification('Failed to load games', 'error');
    }
}

// Update selectGame function
async function selectGame(gameSlug) {
    try {
        debugLog('Selecting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`);
        
        if (!response.ok) {
            throw new Error(`Failed to select game: ${response.statusText}`);
        }
        
        const game = await response.json();
        currentGame = game;
        
        // Update current game display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${game.title}`;
        }
        
        // Stay on games tab and refresh the list
        showTab('games');
        loadGames();
        
        showNotification(`Selected game: ${game.title}`, 'success');
        
    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification(`Failed to select game: ${error.message}`, 'error');
    }
}

// Update loadAssets function
async function loadAssets() {
    if (!currentGame) {
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading assets for game', { 
            gameId: currentGame.id, 
            gameSlug: currentGame.slug 
        });

        const response = await fetch(`/api/assets?game_id=${currentGame.id}`);
        const data = await response.json();
        currentAssets = data.assets;  // Store the loaded assets
        debugLog('Loaded Assets', currentAssets);

        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '';

        if (!currentAssets || currentAssets.length === 0) {
            assetList.innerHTML = '<p class="text-gray-400 text-center p-4">No assets found for this game</p>';
            return;
        }

        currentAssets.forEach(asset => {
            const assetCard = document.createElement('div');
            assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            assetCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    <img src="${asset.imageUrl}" 
                         alt="${asset.name}" 
                         class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                </div>
                <h3 class="font-bold text-lg truncate text-gray-100">${asset.name}</h3>
                <p class="text-sm text-gray-400 mb-2">ID: ${asset.assetId}</p>
                <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${asset.description || 'No description'}</p>
                <div class="flex space-x-2">
                    <button onclick="editAsset('${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="deleteAsset('${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>
            `;
            assetList.appendChild(assetCard);
        });
    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading assets</p>';
    }
}

// Update loadNPCs function with consistent field names
async function loadNPCs() {
    if (!currentGame) {
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading NPCs for game', { 
            gameId: currentGame.id, 
            gameSlug: currentGame.slug 
        });

        const response = await fetch(`/api/npcs?game_id=${currentGame.id}`);
        const data = await response.json();
        currentNPCs = data.npcs;
        debugLog('Loaded NPCs', currentNPCs);

        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '';

        if (!currentNPCs || currentNPCs.length === 0) {
            npcList.innerHTML = '<p class="text-gray-400 text-center p-4">No NPCs found for this game</p>';
            return;
        }

        currentNPCs.forEach(npc => {
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
                    <button onclick="editNPC('${npc.npcId}')" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="deleteNPC('${npc.npcId}')" 
                            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>
            `;
            npcList.appendChild(npcCard);
        });
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading NPCs</p>';
    }
}

// Add notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'error' ? 'bg-red-600' : 
        type === 'success' ? 'bg-green-600' : 
        'bg-blue-600'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 3000);
    }, 3000);
}

// Debug logging helper
function debugLog(title, data) {
    console.log(`=== ${title} ===`);
    console.log(JSON.stringify(data, null, 2));
    console.log('=================');
}

// Add modal handling functions
function editAsset(assetId) {
    debugLog('Editing asset', { assetId });
    try {
        // Find asset in stored data
        const asset = currentAssets.find(a => a.assetId === assetId);
        if (!asset) {
            throw new Error(`Asset not found: ${assetId}`);
        }
        debugLog('Found asset to edit', asset);

        // Populate modal
        document.getElementById('editAssetId').value = asset.assetId;
        document.getElementById('editAssetName').value = asset.name;
        document.getElementById('editAssetDescription').value = asset.description || '';
        document.getElementById('editAssetImage').src = asset.imageUrl || '';
        document.getElementById('editAssetId_display').textContent = `(ID: ${asset.assetId})`;

        // Show modal
        document.getElementById('assetEditModal').style.display = 'block';
    } catch (error) {
        console.error('Error opening asset edit modal:', error);
        showNotification('Failed to open edit modal', 'error');
    }
}

// Update editNPC function with consistent field names
function editNPC(npcId) {
    debugLog('Editing NPC', { npcId });
    try {
        const npc = currentNPCs.find(n => n.npcId === npcId);
        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }
        debugLog('Found NPC to edit', npc);

        document.getElementById('editNpcId').value = npc.npcId;
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcModel').value = npc.model || '';
        document.getElementById('editNpcRadius').value = npc.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npc.systemPrompt || '';

        const abilitiesContainer = document.getElementById('editAbilitiesCheckboxes');
        populateAbilityCheckboxes(abilitiesContainer, npc.abilities || []);

        document.getElementById('npcEditModal').style.display = 'block';
    } catch (error) {
        console.error('Error opening NPC edit modal:', error);
        showNotification('Failed to open edit modal', 'error');
    }
}

// Add save functions
async function saveAssetEdit(event) {
    event.preventDefault();
    const assetId = document.getElementById('editAssetId').value;
    
    try {
        const data = {
            name: document.getElementById('editAssetName').value,
            description: document.getElementById('editAssetDescription').value
        };

        const response = await fetch(`/api/assets/${assetId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to update asset');

        showNotification('Asset updated successfully', 'success');
        closeAssetEditModal();
        loadAssets();  // Reload assets to show changes
    } catch (error) {
        console.error('Error saving asset:', error);
        showNotification('Failed to save changes', 'error');
    }
}

// Update saveNPCEdit function to include assetId
async function saveNPCEdit(event) {
    event.preventDefault();
    const npcId = document.getElementById('editNpcId').value;
    
    try {
        debugLog('Saving NPC edit', { npcId });
        
        const selectedAbilities = Array.from(
            document.querySelectorAll('#editAbilitiesCheckboxes input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        // Find the NPC in our current data to get its assetId
        const npc = currentNPCs.find(n => n.npcId === npcId);
        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            model: document.getElementById('editNpcModel').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            systemPrompt: document.getElementById('editNpcPrompt').value,
            abilities: selectedAbilities,
            assetId: npc.assetId  // Include the existing assetId
        };

        debugLog('Update data:', data);
        
        // Use the database ID for the API call
        const response = await fetch(`/api/npcs/${npc.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to update NPC');

        showNotification('NPC updated successfully', 'success');
        closeNPCEditModal();
        loadNPCs();  // Reload NPCs to show changes
    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes', 'error');
    }
}

// Add close modal functions
function closeAssetEditModal() {
    document.getElementById('assetEditModal').style.display = 'none';
}

function closeNPCEditModal() {
    document.getElementById('npcEditModal').style.display = 'none';
}

// Add click-outside handlers for modals
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Add ability checkbox population function (uses ABILITY_CONFIG from abilityConfig.js)
function populateAbilityCheckboxes(container, selectedAbilities = []) {
    if (!container) {
        console.error('Container not found for abilities!');
        return;
    }

    container.innerHTML = '';
    Object.entries(ABILITY_CONFIG).forEach(([key, ability]) => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-2';
        div.innerHTML = `
            <input type="checkbox" 
                   id="ability_${key}" 
                   name="abilities" 
                   value="${key}"
                   ${selectedAbilities.includes(key) ? 'checked' : ''}
                   class="form-checkbox h-4 w-4 text-blue-600">
            <label for="ability_${key}" class="flex items-center space-x-2">
                <i class="${ability.icon}"></i>
                <span>${ability.label}</span>
            </label>
        `;
        container.appendChild(div);
    });
}

// Add game editing functions
async function editGame(gameSlug) {
    try {
        debugLog('Editing game', { gameSlug });
        // Fetch the game data
        const response = await fetch(`/api/games/${gameSlug}`);
        const game = await response.json();
        
        // Create modal dynamically
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-bold text-blue-400">Edit Game</h2>
                    <button onclick="this.closest('.modal').remove()"
                        class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
                </div>
                <form id="edit-game-form" class="space-y-4">
                    <input type="hidden" id="edit-game-slug" value="${gameSlug}">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Title</label>
                        <input type="text" id="edit-game-title" value="${game.title}" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Description</label>
                        <textarea id="edit-game-description" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
                    </div>
                    <div class="flex justify-end space-x-4">
                        <button type="button" onclick="this.closest('.modal').remove()"
                            class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">Cancel</button>
                        <button type="submit"
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Save Changes</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        // Add submit handler
        document.getElementById('edit-game-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const slug = document.getElementById('edit-game-slug').value;
            const title = document.getElementById('edit-game-title').value;
            const description = document.getElementById('edit-game-description').value;

            try {
                const response = await fetch(`/api/games/${slug}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title, description })
                });

                if (!response.ok) throw new Error('Failed to update game');
                
                showNotification('Game updated successfully', 'success');
                modal.remove();
                loadGames();  // Reload games list
            } catch (error) {
                console.error('Error updating game:', error);
                showNotification('Failed to update game', 'error');
            }
        });
    } catch (error) {
        console.error('Error editing game:', error);
        showNotification('Failed to edit game', 'error');
    }
}

async function deleteGame(gameSlug) {
    if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
        return;
    }
    
    try {
        debugLog('Deleting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete game');
        
        showNotification('Game deleted successfully', 'success');
        loadGames();  // Reload games list
    } catch (error) {
        console.error('Error deleting game:', error);
        showNotification('Failed to delete game', 'error');
    }
}

// Add form handler
document.addEventListener('DOMContentLoaded', function() {
    const assetForm = document.getElementById('assetForm');
    if (assetForm) {
        assetForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            if (!currentGame) {
                showNotification('Please select a game first', 'error');
                return;
            }

            const submitBtn = document.getElementById('submitAssetBtn');
            submitBtn.disabled = true;

            try {
                const formData = new FormData(this);
                formData.set('game_id', currentGame.id);
                
                console.log('Submitting form with data:', {
                    game_id: formData.get('game_id'),
                    asset_id: formData.get('asset_id'),
                    name: formData.get('name'),
                    type: formData.get('type'),
                    file: formData.get('file').name
                });

                const response = await fetch('/api/assets/create', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to create asset');
                }

                const result = await response.json();
                console.log('Asset created:', result);
                
                showNotification('Asset created successfully', 'success');
                this.reset();
                loadAssets();
                
            } catch (error) {
                console.error('Error creating asset:', error);
                showNotification(error.message, 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
});

// Add this function to populate asset selector
async function populateAssetSelector() {
    if (!currentGame) {
        console.log('No game selected for asset selector');
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${currentGame.id}`);
        const data = await response.json();
        
        const assetSelect = document.querySelector('select[name="assetID"]');
        if (assetSelect) {
            // Clear existing options
            assetSelect.innerHTML = '<option value="">Select an asset...</option>';
            
            // Add options for each asset
            data.assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.assetId;
                option.textContent = `${asset.name} (${asset.assetId})`;
                assetSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading assets for selector:', error);
        showNotification('Failed to load assets for selection', 'error');
    }
}

// Add NPC form submission handler
async function handleNPCSubmit(event) {
    event.preventDefault();
    console.log('NPC form submitted');

    if (!currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    try {
        const form = event.target;
        const formData = new FormData(form);
        formData.set('game_id', currentGame.id);
        
        // Get selected abilities
        const abilities = [];
        form.querySelectorAll('input[name="abilities"]:checked').forEach(checkbox => {
            abilities.push(checkbox.value);
        });
        formData.set('abilities', JSON.stringify(abilities));
        
        debugLog('Submitting NPC', {
            game_id: formData.get('game_id'),
            displayName: formData.get('displayName'),
            assetID: formData.get('assetID'),
            system_prompt: formData.get('system_prompt'),
            abilities: formData.get('abilities')
        });

        const response = await fetch('/api/npcs', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create NPC');
        }

        const result = await response.json();
        console.log('NPC created:', result);
        
        showNotification('NPC created successfully', 'success');
        form.reset();
        
        // Refresh the NPCs list
        loadNPCs();
        
    } catch (error) {
        console.error('Error creating NPC:', error);
        showNotification(error.message, 'error');
    }
}

// Add this to the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...

    // Add NPC form handler
    const npcForm = document.getElementById('npcForm');
    if (npcForm) {
        npcForm.addEventListener('submit', handleNPCSubmit);
    }
});







