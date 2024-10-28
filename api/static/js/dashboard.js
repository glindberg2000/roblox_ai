// Dashboard state
let currentTab = 'assets';

// Initial state and utilities
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    loadAssets();
    loadNPCs();
    loadPlayers();
    populateAssetSelect();

    // Initialize ability checkboxes for both create and edit forms
    const createAbilitiesContainer = document.getElementById('abilitiesCheckboxes');
    const editAbilitiesContainer = document.getElementById('editAbilitiesCheckboxes');
    
    console.log('Ability containers:', { 
        create: createAbilitiesContainer, 
        edit: editAbilitiesContainer 
    });

    populateAbilityCheckboxes(createAbilitiesContainer);
    populateAbilityCheckboxes(editAbilitiesContainer);
});

// Show/hide tabs
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    currentTab = tabName;

    if (tabName === 'assets') loadAssets();
    else if (tabName === 'npcs') {
        loadNPCs();
        populateAssetSelect();
    }
    else if (tabName === 'players') loadPlayers();

    // Add this part to populate abilities when switching to NPCs tab
    if (tabName === 'npcs') {
        const createAbilitiesContainer = document.getElementById('abilitiesCheckboxes');
        if (createAbilitiesContainer) {
            populateAbilityCheckboxes(createAbilitiesContainer);
        }
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-blue-600'
        } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Debug logging
function debugLog(title, data) {
    console.log(`=== ${title} ===`);
    console.log(JSON.stringify(data, null, 2));
    console.log('=================');
}

// Asset Management
async function populateAssetSelect(selectElement = document.getElementById('assetSelect')) {
    try {
        const response = await fetch('/api/assets');
        const data = await response.json();
        debugLog('Asset Select Options', data.assets);

        selectElement.innerHTML = '<option value="">Select an asset...</option>';
        data.assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.assetId;
            option.textContent = `${asset.name} (${asset.assetId})`;
            selectElement.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading assets for select:', error);
        showNotification('Failed to load assets for selection', 'error');
    }
}

async function createAsset(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const fileInput = form.querySelector('input[type="file"]');

    try {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            if (file.name.endsWith('.rbxmx') || file.name.endsWith('.rbxm')) {
                const parseFormData = new FormData();
                parseFormData.append('file', file);

                const parseResponse = await fetch('/api/parse-rbxmx', {
                    method: 'POST',
                    body: parseFormData
                });

                if (parseResponse.ok) {
                    const parseData = await parseResponse.json();
                    if (parseData.sourceAssetId) {
                        form.querySelector('[name="assetId"]').value = parseData.sourceAssetId;
                    }
                    if (parseData.name) {
                        form.querySelector('[name="name"]').value = parseData.name;
                    }
                }
            }
        }

        const assetData = {
            assetId: form.querySelector('[name="assetId"]').value,
            name: form.querySelector('[name="name"]').value
        };

        debugLog('Creating Asset', assetData);

        const submitFormData = new FormData();
        submitFormData.append('data', JSON.stringify(assetData));
        if (fileInput.files.length > 0) {
            submitFormData.append('file', fileInput.files[0]);
        }

        const response = await fetch('/api/assets', {
            method: 'POST',
            body: submitFormData
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        showNotification('Asset created successfully!', 'success');
        await loadAssets();
        form.reset();

    } catch (error) {
        console.error('Error creating asset:', error);
        showNotification('Failed to create asset: ' + error.message, 'error');
    }
}

async function loadAssets() {
    try {
        const response = await fetch('/api/assets');
        const data = await response.json();
        debugLog('Loaded Assets', data.assets);

        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '';

        data.assets.forEach(asset => {
            const safeAsset = {
                assetId: asset.assetId || '',
                name: asset.name || 'Unnamed Asset',
                description: asset.description || '',
                imageUrl: asset.imageUrl || ''
            };

            const assetCard = document.createElement('div');
            assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';

            // Use data attributes instead of onclick
            assetCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    <img src="${safeAsset.imageUrl}" 
                         alt="${safeAsset.name}" 
                         class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                </div>
                <h3 class="font-bold text-lg truncate text-gray-100">${safeAsset.name}</h3>
                <p class="text-sm text-gray-400 mb-2">ID: ${safeAsset.assetId}</p>
                <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${safeAsset.description}</p>
                <div class="flex space-x-2">
                    <button data-asset='${JSON.stringify(safeAsset).replace(/'/g, "&apos;")}' 
                            class="edit-asset-btn flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button data-id="${safeAsset.assetId}" 
                            class="delete-asset-btn flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>`;

            assetList.appendChild(assetCard);
        });

        // Add event listeners after creating cards
        document.querySelectorAll('.edit-asset-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const assetData = JSON.parse(this.dataset.asset);
                handleAssetEdit(assetData);
            });
        });

        document.querySelectorAll('.delete-asset-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                deleteItem('asset', this.dataset.id);
            });
        });

    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
    }
}

// NPC Management
async function createNPC(event) {
    event.preventDefault();

    try {
        const form = event.target;
        // Add this to get selected abilities
        const selectedAbilities = Array.from(form.querySelectorAll('input[name="abilities"]:checked'))
            .map(checkbox => checkbox.value);

        const npcData = {
            displayName: form.displayName.value,
            model: form.displayName.value.replace(/\s+/g, ''),
            responseRadius: parseInt(form.responseRadius.value),
            assetID: form.assetID.value || null,
            system_prompt: form.system_prompt.value,
            spawnPosition: {
                x: parseFloat(form.spawnX.value),
                y: parseFloat(form.spawnY.value),
                z: parseFloat(form.spawnZ.value)
            },
            abilities: selectedAbilities
        };

        debugLog('Creating NPC', npcData);

        const response = await fetch('/api/npcs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(npcData)
        });

        if (!response.ok) throw new Error('Failed to create NPC');

        showNotification('NPC created successfully!', 'success');
        form.reset();
        loadNPCs();
    } catch (error) {
        console.error('Error creating NPC:', error);
        showNotification('Failed to create NPC: ' + error.message, 'error');
    }
}

async function loadNPCs() {
    try {
        const response = await fetch('/api/npcs');
        const data = await response.json();
        debugLog('Raw NPC Data:', data.npcs);

        // Fetch assets first to ensure we have the data
        const assetsResponse = await fetch('/api/assets');
        const assetsData = await assetsResponse.json();
        const assetsMap = new Map(assetsData.assets.map(asset => [asset.assetId, asset]));

        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '';

        data.npcs.forEach(npc => {
            const associatedAsset = npc.assetId ? assetsMap.get(npc.assetId) : null;

            // Add abilities display to the card
            const abilitiesHTML = (npc.abilities || []).map(ability => {
                const abilityConfig = ABILITY_CONFIG[ability];
                return abilityConfig ? 
                    `<i class="${abilityConfig.icon}" title="${abilityConfig.label}" class="text-gray-300 mr-2"></i>` : 
                    '';
            }).join('');

            const npcCard = document.createElement('div');
            npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';

            npcCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    ${associatedAsset?.imageUrl ?
                    `<img src="${associatedAsset.imageUrl}" 
                          alt="${npc.displayName}" 
                          class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">` :
                    '<div class="w-full h-32 bg-dark-700 rounded-lg flex items-center justify-center text-gray-400">No Image</div>'}
                </div>
                <h3 class="font-bold text-lg text-gray-100">${npc.displayName || 'Unnamed NPC'}</h3>
                <p class="text-sm text-gray-400 mb-1">Model: ${npc.model || 'No Model'}</p>
                <p class="text-sm text-gray-400 mb-1">Name: ${associatedAsset?.name || 'None'}</p>
                <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId || 'None'}</p>
                <p class="text-sm mb-2 text-gray-300">Radius: ${npc.responseRadius || 20}m</p>
                <div class="text-sm mb-4 h-20 overflow-y-auto">
                    <p class="font-medium text-gray-300">Personality:</p>
                    <p class="text-gray-400">${npc.system_prompt || 'No personality defined'}</p>
                </div>
                <div class="flex flex-wrap gap-2 mb-4">
                    ${abilitiesHTML}
                </div>
                <div class="flex space-x-2">
                    <button data-npc='${JSON.stringify(npc).replace(/'/g, "&apos;")}' 
                            class="edit-npc-btn flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button data-id="${npc.id}" 
                            class="delete-npc-btn flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>`;

            npcList.appendChild(npcCard);
        });

        // Add event listeners after creating cards
        document.querySelectorAll('.edit-npc-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const npcData = JSON.parse(this.dataset.npc);
                handleNPCEdit(npcData);
            });
        });

        document.querySelectorAll('.delete-npc-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                deleteItem('npc', this.dataset.id);
            });
        });

    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
    }
}
function handleNPCEdit(npcData) {
    try {
        // If npcData is a string, parse it
        const data = typeof npcData === 'string' ? JSON.parse(npcData) : npcData;
        debugLog('Opening NPC Edit Modal', data);

        const modal = document.getElementById('npcEditModal');
        if (!modal) throw new Error('Modal element not found');

        // Populate form fields
        document.getElementById('editNpcId').value = data.id;
        document.getElementById('editNpcDisplayName').value = data.displayName || '';
        document.getElementById('editNpcRadius').value = data.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = data.system_prompt || '';

        const spawnPos = data.spawnPosition || { x: 0, y: 5, z: 0 };
        document.getElementById('editNpcSpawnX').value = spawnPos.x || 0;
        document.getElementById('editNpcSpawnY').value = spawnPos.y || 5;
        document.getElementById('editNpcSpawnZ').value = spawnPos.z || 0;

        // Set asset ID if it exists
        const assetSelect = document.getElementById('editNpcAssetId');
        if (assetSelect) {
            populateAssetSelect(assetSelect).then(() => {
                assetSelect.value = data.assetId || '';
            });
        }

        // Populate abilities checkboxes with current selections
        populateAbilityCheckboxes(
            document.getElementById('editAbilitiesCheckboxes'), 
            data.abilities || []
        );

        modal.style.display = 'block';
    } catch (error) {
        console.error('Error showing NPC edit modal:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}

function handleAssetEdit(asset) {
    try {
        debugLog('Editing Asset', asset);
        const modal = document.getElementById('assetEditModal');

        // Parse the asset if it's a string (from JSON.stringify)
        const assetData = typeof asset === 'string' ? JSON.parse(asset) : asset;

        // Populate the edit form
        document.getElementById('editAssetId').value = assetData.assetId;
        document.getElementById('editAssetName').value = assetData.name || '';
        document.getElementById('editAssetDescription').value = assetData.description || '';

        // Only try to set image if element exists
        const imageElement = document.getElementById('editAssetImage');
        if (imageElement) {
            imageElement.src = assetData.imageUrl || '';
        }

        const idDisplay = document.getElementById('editAssetId_display');
        if (idDisplay) {
            idDisplay.textContent = `(ID: ${assetData.assetId})`;
        }

        modal.style.display = 'block';
    } catch (error) {
        console.error('Error showing asset edit modal:', error);
        showNotification('Failed to open asset edit modal', 'error');
    }
}

function showNPCEditModal(npcData) {
    try {
        debugLog('Opening NPC Edit Modal', npcData);
        const modal = document.getElementById('npcEditModal');
        if (!modal) throw new Error('Modal element not found');

        // Populate form fields
        document.getElementById('editNpcId').value = npcData.id;
        document.getElementById('editNpcDisplayName').value = npcData.displayName || '';
        document.getElementById('editNpcRadius').value = npcData.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npcData.system_prompt || '';

        const spawnPos = npcData.spawnPosition || { x: 0, y: 5, z: 0 };
        document.getElementById('editNpcSpawnX').value = spawnPos.x || 0;
        document.getElementById('editNpcSpawnY').value = spawnPos.y || 5;
        document.getElementById('editNpcSpawnZ').value = spawnPos.z || 0;

        // Make assetID optional
        const assetSelect = document.getElementById('editNpcAssetId');
        assetSelect.removeAttribute('required');

        // Populate asset select
        populateAssetSelect(assetSelect)
            .then(() => {
                assetSelect.value = npcData.assetId || '';
                debugLog('Asset Select Value Set', { value: assetSelect.value });
            });

        modal.style.display = 'block';
    } catch (error) {
        console.error('Error showing NPC edit modal:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}

function closeNPCEditModal() {
    document.getElementById('npcEditModal').style.display = 'none';
}

function closeAssetEditModal() {
    document.getElementById('assetEditModal').style.display = 'none';
}

async function saveNPCEdit(event) {
    event.preventDefault();

    try {
        const npcId = document.getElementById('editNpcId').value;
        const assetId = document.getElementById('editNpcAssetId').value;

        // Get selected abilities
        const selectedAbilities = Array.from(
            document.querySelectorAll('#editAbilitiesCheckboxes input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        // Get current NPC data
        const npcResponse = await fetch(`/api/npcs/${npcId}`);
        const currentNPC = await npcResponse.json();

        const npcData = {
            id: npcId,
            displayName: document.getElementById('editNpcDisplayName').value,
            assetId: assetId,
            model: currentNPC.model,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value) || 20,
            spawnPosition: {
                x: parseFloat(document.getElementById('editNpcSpawnX').value) || 0,
                y: parseFloat(document.getElementById('editNpcSpawnY').value) || 5,
                z: parseFloat(document.getElementById('editNpcSpawnZ').value) || 0
            },
            system_prompt: document.getElementById('editNpcPrompt').value || '',
            shortTermMemory: [],
            abilities: selectedAbilities // Add selected abilities
        };

        debugLog('=== NPC Update Payload: ===');
        debugLog(JSON.stringify(npcData, null, 2));
        debugLog('=================');

        const response = await fetch(`/api/npcs/${npcId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(npcData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Server Error Response:', errorData);
            throw new Error(errorData.detail || `Failed to update NPC: ${response.status}`);
        }

        showNotification('NPC updated successfully', 'success');
        closeNPCEditModal();
        await loadNPCs();
    } catch (error) {
        console.error('Error updating NPC:', error);
        showNotification('Failed to update NPC: ' + error.message, 'error');
    }
}
async function saveAssetEdit(event) {
    event.preventDefault();
    try {
        const assetId = document.getElementById('editAssetId').value;
        const assetData = {
            assetId: assetId, // Include the assetId in the payload
            name: document.getElementById('editAssetName').value,
            description: document.getElementById('editAssetDescription').value || '',
            // Include any other required fields from your API schema
        };

        debugLog('Saving Asset Edit', { id: assetId, data: assetData });

        const response = await fetch(`/api/assets/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(assetData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update asset');
        }

        showNotification('Asset updated successfully', 'success');
        closeAssetEditModal();
        await loadAssets();
    } catch (error) {
        console.error('Error updating asset:', error);
        showNotification('Failed to update asset: ' + error.message, 'error');
    }
}

async function deleteItem(type, id) {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) return;

    try {
        debugLog('Deleting Item', { type, id });
        const response = await fetch(`/api/${type}s/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete item');

        showNotification(`${type} deleted successfully`, 'success');

        if (type === 'asset') await loadAssets();
        else if (type === 'npc') await loadNPCs();
        else if (type === 'player') await loadPlayers();

    } catch (error) {
        console.error('Error deleting item:', error);
        showNotification('Failed to delete item', 'error');
    }
}



// Modal click-outside handlers
window.onclick = function (event) {
    const editModal = document.getElementById('editModal');
    const npcEditModal = document.getElementById('npcEditModal');
    const assetEditModal = document.getElementById('assetEditModal');

    if (event.target === editModal) {
        closeEditModal();
    } else if (event.target === npcEditModal) {
        closeNPCEditModal();
    } else if (event.target === assetEditModal) {
        closeAssetEditModal();
    }
}

// Add these new functions for ability handling
function populateAbilityCheckboxes(container, selectedAbilities = []) {
    console.log('Populating abilities:', { container, selectedAbilities });
    if (!container) {
        console.error('Container not found for abilities!');
        return;
    }
    
    // Verify ABILITY_CONFIG is available
    if (!ABILITY_CONFIG) {
        console.error('ABILITY_CONFIG is not defined!');
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
    
    console.log('Abilities populated:', container.innerHTML);
}



