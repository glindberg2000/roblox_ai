function debugLog(title, data) {
    console.log(`=== ${title} ===`);
    console.log(JSON.stringify(data, null, 2));
    console.log('=================');
}

let currentNPCs = [];  // Store loaded NPCs

async function saveNPCEdit(event) {
    event.preventDefault();
    const npcId = document.getElementById('editNpcId').value;

    try {
        if (!currentGame) {
            throw new Error('No game selected');
        }

        const selectedAbilities = Array.from(
            document.querySelectorAll('#editAbilitiesCheckboxes input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            assetId: document.getElementById('editNpcModel').value,
            systemPrompt: document.getElementById('editNpcPrompt').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            abilities: selectedAbilities
        };

        console.log('Sending NPC update:', {
            npcId,
            gameId: currentGame.id,
            data
        });

        const response = await fetch(`/api/npcs/${npcId}?game_id=${currentGame.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update NPC');
        }

        closeNPCEditModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Reload NPCs to show changes

    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes: ' + error.message, 'error');
    }
}

function editNPC(npcId) {
    console.log('Edit clicked with ID:', npcId, 'Type:', typeof npcId);
    console.log('Current NPCs:', currentNPCs);
    currentNPCs.forEach(n => {
        console.log('NPC ID:', n.id, 'Type:', typeof n.id);
    });

    try {
        if (!currentGame) {
            showNotification('Please select a game first', 'error');
            return;
        }

        // Find NPC using id instead of npcId and ensure string comparison
        const npc = currentNPCs.find(n => String(n.id) === String(npcId));
        if (!npc) {
            console.error('NPC lookup failed:', {
                lookingFor: npcId,
                availableNPCs: currentNPCs.map(n => ({
                    id: n.id,
                    npcId: n.npcId,
                    displayName: n.displayName
                }))
            });
            throw new Error(`NPC not found: ${npcId}`);
        }
        debugLog('Found NPC to edit', npc);

        // Populate form fields
        document.getElementById('editNpcId').value = npc.id;  // Changed from npcId to id
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcModel').value = npc.assetId;
        document.getElementById('editNpcRadius').value = npc.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npc.systemPrompt || '';

        // Show modal
        const modal = document.getElementById('npcEditModal');
        if (modal) {
            modal.style.display = 'block';
        } else {
            console.error('NPC edit modal not found');
        }
    } catch (error) {
        console.error('Error opening NPC edit modal:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}

// Add this to ensure the function is globally available
window.editNPC = editNPC;
window.deleteNPC = deleteNPC;

function loadNPCs() {
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

        fetch(`/api/npcs?game_id=${currentGame.id}`)
            .then(response => response.json())
            .then(data => {
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
                            <button onclick="editNPC(${npc.id})" 
                                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                                Edit
                            </button>
                            <button onclick="deleteNPC(${npc.id})" 
                                    class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                                Delete
                            </button>
                        </div>
                    `;
                    npcList.appendChild(npcCard);
                });
            });
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading NPCs</p>';
    }

    // Add modal HTML if it doesn't exist
    if (!document.getElementById('npcEditModal')) {
        const modalHTML = `
            <div id="npcEditModal" class="modal">
                <div class="modal-content max-w-2xl">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
                        <button onclick="closeNPCEditModal()"
                            class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
                    </div>
                    <form id="npcEditForm" onsubmit="saveNPCEdit(event)" class="space-y-6">
                        <input type="hidden" id="editNpcId">
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                            <input type="text" id="editNpcDisplayName" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                            <input type="text" id="editNpcModel" required
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                            <input type="number" id="editNpcRadius" required min="1" max="100"
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                            <textarea id="editNpcPrompt" required rows="4"
                                class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"></textarea>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                            <div id="editAbilitiesCheckboxes" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                                <!-- Will be populated via JavaScript -->
                            </div>
                        </div>
                        <div class="flex justify-end space-x-4 pt-4">
                            <button type="button" onclick="closeNPCEditModal()"
                                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                                Cancel
                            </button>
                            <button type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Make it globally available
window.closeNPCEditModal = closeNPCEditModal;

async function loadAssetOptions() {
    if (!currentGame) return;

    try {
        const response = await fetch(`/api/assets?game_id=${currentGame.id}`);
        const data = await response.json();

        const assetSelect = document.getElementById('assetSelect');
        if (!assetSelect) {
            console.error('Asset select element not found');
            return;
        }

        // Add debug logging
        console.log('Found select element:', assetSelect);
        console.log('Loading assets:', data.assets);

        assetSelect.innerHTML = '<option value="">Select an asset...</option>';

        data.assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.asset_id;
            option.textContent = asset.name;
            assetSelect.appendChild(option);
            console.log(`Added option: ${asset.name} (${asset.asset_id})`);
        });
    } catch (error) {
        console.error('Error loading assets:', error);
    }
}

// Call this when showing NPC create form
loadAssetOptions();

// Add game selection handler
function setCurrentGame(game) {
    currentGame = game;
    // Set the hidden game_id field
    const gameIdField = document.getElementById('createNpcGameId');
    if (gameIdField) {
        gameIdField.value = game.id;
        console.log('Set game ID to:', game.id);
    }

    // Update display
    document.getElementById('currentGameDisplay').textContent = `Current Game: ${game.title}`;

    // Load assets for the game
    loadAssetOptions();
}

async function createNPC(event) {
    event.preventDefault();
    console.log('createNPC called');

    try {
        if (!currentGame) {
            console.log('No game selected');
            throw new Error('No game selected');
        }

        const formData = new FormData(event.target);
        formData.set('game_id', currentGame.id);

        // Debug form data
        console.log('Form data being sent:');
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }

        const response = await fetch('/api/npcs', {
            method: 'POST',
            body: formData
        });

        const responseText = await response.text();
        console.log('Raw response:', responseText);

        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse response:', e);
            throw new Error('Invalid server response');
        }

        if (!response.ok) {
            // Handle FastAPI validation errors
            if (response.status === 422) {
                const errors = result.detail;
                // Format validation errors
                const errorMessages = errors.map(err =>
                    `${err.loc.join('.')}: ${err.msg}`
                ).join('\n');
                throw new Error(errorMessages);
            }
            throw new Error(result.detail || 'Failed to create NPC');
        }

        console.log('NPC created successfully');
        showNotification('NPC created successfully', 'success');
        loadNPCs();

    } catch (error) {
        console.error('Error in createNPC:', {
            error,
            name: error.name,
            message: error.message,
            status: error.status
        });

        // Show the actual validation error message
        showNotification(error.message || 'Failed to create NPC', 'error');
    }
}

// Add tab switching handler
document.getElementById('nav-npcs').addEventListener('click', function () {
    // Show NPCs tab
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.getElementById('npcsTab').style.display = 'block';

    // Load assets for select
    loadAssetOptions();
});

// Load assets if NPCs tab is active on page load
if (document.getElementById('npcsTab').style.display !== 'none') {
    loadAssetOptions();
}

// Make functions globally available
window.setCurrentGame = setCurrentGame;
window.createNPC = createNPC;

function showNotification(message, type = 'info') {
    console.log('showNotification called with:', {
        message: message,
        type: type,
        messageType: typeof message
    });

    // Ensure message is a string
    const displayMessage = typeof message === 'object' ?
        JSON.stringify(message) : String(message);

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg ${type === 'error' ? 'bg-red-500' : 'bg-green-500'
        } text-white`;
    notification.textContent = displayMessage;

    // Add to document
    document.body.appendChild(notification);

    // Remove after delay
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}







