import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

export async function loadNPCs() {
    if (!state.currentGame) {
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading NPCs for game', {
            gameId: state.currentGame.id,
            gameSlug: state.currentGame.slug
        });

        const response = await fetch(`/api/npcs?game_id=${state.currentGame.id}`);
        const data = await response.json();
        state.currentNPCs = data.npcs;
        debugLog('Loaded NPCs', state.currentNPCs);

        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '';

        if (!state.currentNPCs || state.currentNPCs.length === 0) {
            npcList.innerHTML = '<p class="text-gray-400 text-center p-4">No NPCs found for this game</p>';
            return;
        }

        state.currentNPCs.forEach(npc => {
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
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading NPCs</p>';
    }
}

export async function editNPC(npcId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const npc = state.currentNPCs.find(n => n.npcId === npcId);
    if (!npc) {
        showNotification('NPC not found', 'error');
        return;
    }

    // Fetch available models (assets)
    const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
    const data = await response.json();
    const availableModels = data.assets || [];

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
                <input type="text" id="editNpcDisplayName" value="${npc.displayName}" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
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

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                <select id="editNpcModel" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    ${availableModels.map(model => `
                        <option value="${model.assetId}" ${model.assetId === npc.assetId ? 'selected' : ''}>
                            ${model.name}
                        </option>
                    `).join('')}
                </select>
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

    showModal(modalContent);

    // Add form submit handler
    const form = modalContent.querySelector('form');
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveNPCEdit(npcId);
    };
}

export async function saveNPCEdit(npcId) {
    try {
        const form = document.getElementById('editNPCForm');
        const selectedAbilities = Array.from(
            form.querySelectorAll('input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            systemPrompt: document.getElementById('editNpcPrompt').value,
            abilities: selectedAbilities,
            assetId: state.currentNPCs.find(n => n.npcId === npcId).assetId
        };

        const response = await fetch(`/api/npcs/${npcId}?game_id=${state.currentGame.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to update NPC');
        }

        hideModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Refresh the list
    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes', 'error');
    }
}

// Add delete function
export async function deleteNPC(npcId) {
    if (!confirm('Are you sure you want to delete this NPC?')) {
        return;
    }

    try {
        const response = await fetch(`/api/npcs/${npcId}?game_id=${state.currentGame.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete NPC');
        }

        showNotification('NPC deleted successfully', 'success');
        loadNPCs();
    } catch (error) {
        console.error('Error deleting NPC:', error);
        showNotification('Failed to delete NPC', 'error');
    }
}

// Make functions globally available
window.loadNPCs = loadNPCs;
window.editNPC = editNPC;
window.deleteNPC = deleteNPC;

export async function createNPC(event) {
    event.preventDefault();
    console.log('NPC form submitted');

    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    try {
        const form = event.target;
        const formData = new FormData(form);
        formData.set('game_id', state.currentGame.id);

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

// Add to global window object
window.createNPC = createNPC;