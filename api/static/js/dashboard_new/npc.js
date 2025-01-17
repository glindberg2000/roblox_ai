import { state } from './state.js';
import { showNotification } from './ui.js';
import { showModal } from './ui.js';

// Add version identifier at top
console.log('=== Loading NPC.js v2023-11-22-D ===');

// Add function to fetch available models
async function fetchAvailableModels() {
    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        return data.assets || [];
    } catch (error) {
        console.error('Error fetching models:', error);
        return [];
    }
}

export async function editNPC(npcId) {
    console.log('NPC.JS: editNPC called with:', npcId);
    try {
        // Find NPC using npcId
        const npc = state.currentNPCs.find(n => n.npcId === npcId);
        console.log('NPC data to edit:', npc);

        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }

        // Fetch available models first
        const availableModels = await fetchAvailableModels();
        console.log('Available models:', availableModels);

        // Parse spawn position - handle both string and object formats
        let spawnPosition;
        if (typeof npc.spawnPosition === 'string') {
            spawnPosition = JSON.parse(npc.spawnPosition);
        } else {
            spawnPosition = npc.spawnPosition || { x: 0, y: 5, z: 0 };
        }
        console.log('Parsed spawn position:', spawnPosition);

        // Create modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
            </div>
            <form id="editNPCForm" class="space-y-4">
                <input type="hidden" id="editNpcId" value="${npc.npcId}">
                
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                    <input type="text" id="editNpcDisplayName" value="${npc.displayName || ''}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                    <select id="editNpcModel" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        ${availableModels.map(model => `
                            <option value="${model.asset_id}" ${model.asset_id === npc.assetId ? 'selected' : ''}>
                                ${model.name}
                            </option>
                        `).join('')}
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                    <input type="number" id="editNpcRadius" value="${npc.responseRadius || 20}" required min="1" max="100"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                    <textarea id="editNpcPrompt" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${npc.systemPrompt || ''}</textarea>
                </div>

                <!-- Add spawn position fields -->
                <div class="grid grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn X:</label>
                        <input type="number" id="editNpcSpawnX" value="${spawnPosition.x}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn Y:</label>
                        <input type="number" id="editNpcSpawnY" value="${spawnPosition.y}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn Z:</label>
                        <input type="number" id="editNpcSpawnZ" value="${spawnPosition.z}" step="0.1"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                    <div id="editAbilitiesContainer" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                        ${window.ABILITY_CONFIG.map(ability => `
                            <label class="flex items-center space-x-2">
                                <input type="checkbox" name="abilities" value="${ability.id}"
                                    ${(npc.abilities || []).includes(ability.id) ? 'checked' : ''}
                                    class="form-checkbox h-4 w-4 text-blue-600">
                                <span class="text-gray-300">
                                    <i class="${ability.icon}"></i>
                                    ${ability.name}
                                </span>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="window.hideModal()" 
                        class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                        Cancel
                    </button>
                    <button type="submit" 
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        `;

        // Show modal
        showModal(modalContent);

        // Update form submit handler to include spawn position
        const form = modalContent.querySelector('form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();

                // Get form values
                const formData = {
                    displayName: form.querySelector('#editNpcDisplayName').value.trim(),
                    assetId: form.querySelector('#editNpcModel').value,
                    responseRadius: parseInt(form.querySelector('#editNpcRadius').value) || 20,
                    systemPrompt: form.querySelector('#editNpcPrompt').value.trim(),
                    abilities: Array.from(form.querySelectorAll('input[name="abilities"]:checked')).map(cb => cb.value),
                    // Add spawn position
                    spawnPosition: {
                        x: parseFloat(form.querySelector('#editNpcSpawnX').value) || 0,
                        y: parseFloat(form.querySelector('#editNpcSpawnY').value) || 5,
                        z: parseFloat(form.querySelector('#editNpcSpawnZ').value) || 0
                    }
                };

                console.log('Form data before save:', formData);

                try {
                    const npcUuid = form.querySelector('#editNpcId').value;
                    console.log('Using NPC UUID for save:', npcUuid);
                    await saveNPCEdit(npcUuid, formData);
                } catch (error) {
                    showNotification(error.message, 'error');
                }
            };
        }
    } catch (error) {
        console.error('NPC.JS: Error in editNPC:', error);
        showNotification(error.message, 'error');
    }
}

export async function saveNPCEdit(npcId, data) {
    try {
        console.log('NPC.js v2023-11-22-D: Saving NPC with data:', {
            npcId,
            gameId: state.currentGame.id,
            data
        });

        // Send data directly without additional serialization
        const formattedData = {
            ...data
            // No spawn_position field, just use spawnPosition object
        };

        console.log('Formatted data for backend:', formattedData);

        const response = await fetch(`/api/npcs/${npcId}?game_id=${state.currentGame.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formattedData)
        });

        // Add response debugging
        const responseText = await response.text();
        console.log('Edit response:', responseText);

        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse edit response:', e);
            throw new Error('Invalid server response');
        }

        if (!response.ok) {
            // Handle validation errors
            if (response.status === 422) {
                const errors = result.detail;
                if (Array.isArray(errors)) {
                    const errorMessages = errors.map(err =>
                        `${err.loc.join('.')}: ${err.msg}`
                    ).join('\n');
                    throw new Error(errorMessages);
                }
            }
            throw new Error(result.detail || 'Failed to update NPC');
        }

        hideModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Refresh the list

    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification(error.message, 'error');
        throw error;  // Re-throw to prevent modal close
    }
}

// Add this function to populate abilities in the create form
function populateCreateAbilities() {
    const container = document.getElementById('createAbilitiesContainer');
    if (container && window.ABILITY_CONFIG) {
        container.innerHTML = window.ABILITY_CONFIG.map(ability => `
            <label class="flex items-center space-x-2">
                <input type="checkbox" name="abilities" value="${ability.id}"
                    class="form-checkbox h-4 w-4 text-blue-600">
                <span class="text-gray-300">
                    <i class="${ability.icon}"></i>
                    ${ability.name}
                </span>
            </label>
        `).join('');
    }
}

// Add this function to populate the create form's asset selector
async function populateCreateFormAssets() {
    console.log('Populating create form assets...');
    try {
        const assets = await fetchAvailableModels();
        console.log('Fetched assets:', assets);

        const assetSelect = document.getElementById('assetSelect');
        if (assetSelect) {
            assetSelect.innerHTML = '<option value="">Select a model...</option>';
            assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.asset_id;  // Make sure we're using the right field
                option.textContent = asset.name;
                assetSelect.appendChild(option);
                console.log(`Added option: ${asset.name} (${asset.asset_id})`);
            });
        } else {
            console.error('Asset select element not found');
        }
    } catch (error) {
        console.error('Error populating create form assets:', error);
    }
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', () => {
    populateCreateAbilities();
    populateCreateFormAssets();
});

// Make function globally available
window.editNPC = editNPC;
window.saveNPCEdit = saveNPCEdit;
window.populateCreateAbilities = populateCreateAbilities;
window.populateCreateFormAssets = populateCreateFormAssets;

async function createNPC(event) {
    event.preventDefault();
    console.log('createNPC called from npc.js');

    try {
        if (!state.currentGame) {
            throw new Error('No game selected');
        }

        const formData = new FormData(event.target);
        formData.set('game_id', state.currentGame.id);

        // Get abilities
        const abilities = Array.from(
            event.target.querySelectorAll('input[name="abilities"]:checked')
        ).map(cb => cb.value);
        formData.set('abilities', JSON.stringify(abilities));

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
            console.log('Parsed response:', result);
        } catch (e) {
            console.error('Failed to parse response:', e);
            throw new Error('Invalid server response');
        }

        if (!response.ok) {
            if (response.status === 422) {
                const errors = result.detail;
                if (Array.isArray(errors)) {
                    const errorMessages = errors.map(err =>
                        `${err.loc.join('.')}: ${err.msg}`
                    ).join('\n');
                    throw new Error(errorMessages);
                }
            }
            // If not a validation error, use the detail message
            const errorMessage = typeof result.detail === 'object' ?
                JSON.stringify(result.detail) : result.detail;
            throw new Error(errorMessage || 'Failed to create NPC');
        }

        showNotification('NPC created successfully', 'success');
        loadNPCs();

    } catch (error) {
        console.error('Error in createNPC:', {
            error,
            name: error.name,
            message: error.message,
            response: error.response
        });

        showNotification(error.message || 'Failed to create NPC', 'error');
    }
}

// Make function globally available
window.createNPC = createNPC;

// Make sure we call this when the game is selected
function setCurrentGame(game) {
    state.currentGame = game;
    // Set the hidden game_id field
    const gameIdField = document.getElementById('createNpcGameId');
    if (gameIdField) {
        gameIdField.value = game.id;
        console.log('Set game ID to:', game.id);
    }

    // Update display
    document.getElementById('currentGameDisplay').textContent = `Current Game: ${game.title}`;

    // Load assets for the game
    populateCreateFormAssets();
}