// Dashboard state
let currentTab = 'assets';

// Initial state and utilities
document.addEventListener('DOMContentLoaded', () => {
    loadAssets();
    loadNPCs();
    loadPlayers();
    populateAssetSelect();
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
            const assetCard = document.createElement('div');
            assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            assetCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    <img src="${asset.imageUrl || ''}" 
                         alt="${asset.name}" 
                         class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                </div>
                <h3 class="font-bold text-lg truncate text-gray-100">${asset.name}</h3>
                <p class="text-sm text-gray-400 mb-2">ID: ${asset.assetId}</p>
                <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${asset.description || ''}</p>
                <div class="flex space-x-2">
                    <button onclick='handleAssetEdit(${JSON.stringify(asset).replace(/'/g, "&apos;")})' 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="deleteItem('asset', '${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>`;
            assetList.appendChild(assetCard);
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
            shortTermMemory: []
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
        debugLog('Loaded NPCs', data.npcs);

        const assetsResponse = await fetch('/api/assets');
        const assetsData = await assetsResponse.json();
        debugLog('Available Assets', assetsData.assets);
        const assetsMap = new Map(assetsData.assets.map(asset => [asset.assetId, asset]));

        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '';

        data.npcs.forEach(npc => {
            const associatedAsset = npc.assetID ? assetsMap.get(npc.assetID) : null;
            debugLog(`NPC ${npc.id} Associated Asset`, associatedAsset);

            const npcCard = document.createElement('div');
            npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';

            // Store the complete NPC data as a data attribute
            const npcData = {
                id: npc.id,
                displayName: npc.displayName || '',
                assetID: npc.assetID || '',
                responseRadius: npc.responseRadius || 20,
                system_prompt: npc.system_prompt || '',
                spawnPosition: npc.spawnPosition || { x: 0, y: 5, z: 0 }
            };

            npcCard.dataset.npc = JSON.stringify(npcData);

            npcCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    ${associatedAsset?.imageUrl ?
                    `<img src="${associatedAsset.imageUrl}" 
                              alt="${npc.displayName}" 
                              class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">` :
                    '<div class="w-full h-32 bg-dark-700 rounded-lg flex items-center justify-center text-gray-400">No Image</div>'}
                </div>
                <h3 class="font-bold text-lg text-gray-100">${npc.displayName || 'Unnamed NPC'}</h3>
                <p class="text-sm text-gray-400 mb-1">Asset: ${associatedAsset?.name || 'None'}</p>
                <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetID || 'None'}</p>
                <p class="text-sm mb-2 text-gray-300">Radius: ${npc.responseRadius || 20}m</p>
                <div class="text-sm mb-4 h-20 overflow-y-auto">
                    <p class="font-medium text-gray-300">Personality:</p>
                    <p class="text-gray-400">${npc.system_prompt || 'No personality defined'}</p>
                </div>
                <div class="flex space-x-2">
                    <button onclick="handleNPCEdit(this)" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="deleteItem('npc', '${npc.id}')" 
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
    }
}

function handleNPCEdit(button) {
    try {
        // Visual feedback
        button.classList.add('opacity-75');
        setTimeout(() => button.classList.remove('opacity-75'), 200);

        const npcCard = button.closest('div[data-npc]');
        if (!npcCard) {
            throw new Error('Could not find NPC data container');
        }

        const npcDataStr = npcCard.dataset.npc;
        debugLog('Raw NPC Data', npcDataStr);

        const npcData = JSON.parse(npcDataStr);
        debugLog('Parsed NPC Data', npcData);

        showNPCEditModal(npcData);
    } catch (error) {
        console.error('Error handling NPC edit:', error);
        showNotification('Failed to open edit modal: ' + error.message, 'error');
    }
}

function handleAssetEdit(asset) {
    try {
        debugLog('Editing Asset', asset);
        const modal = document.getElementById('assetEditModal');

        // Parse the asset if it's a string (from JSON.stringify)
        const assetData = typeof asset === 'string' ? JSON.parse(asset) : asset;

        document.getElementById('editAssetId').value = assetData.assetId;
        document.getElementById('editAssetName').value = assetData.name || '';
        document.getElementById('editAssetDescription').value = assetData.description || '';
        document.getElementById('editAssetImage').src = assetData.imageUrl || '';
        document.getElementById('editAssetId_display').textContent = `(ID: ${assetData.assetId})`;

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
                assetSelect.value = npcData.assetID || '';
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
        const npcData = {
            displayName: document.getElementById('editNpcDisplayName').value,
            model: document.getElementById('editNpcDisplayName').value.replace(/\s+/g, ''),
            assetID: document.getElementById('editNpcAssetId').value || null,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value) || 20,
            spawnPosition: {
                x: parseFloat(document.getElementById('editNpcSpawnX').value) || 0,
                y: parseFloat(document.getElementById('editNpcSpawnY').value) || 5,
                z: parseFloat(document.getElementById('editNpcSpawnZ').value) || 0
            },
            system_prompt: document.getElementById('editNpcPrompt').value || ''
        };

        const npcId = document.getElementById('editNpcId').value;
        debugLog('Saving NPC Edit', { id: npcId, data: npcData });

        const response = await fetch(`/api/npcs/${npcId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(npcData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to update NPC');
        }

        showNotification('NPC updated successfully', 'success');
        closeNPCEditModal();
        loadNPCs();
    } catch (error) {
        console.error('Error updating NPC:', error);
        showNotification('Failed to update NPC: ' + error.message, 'error');
    }
}

async function saveAssetEdit(event) {
    event.preventDefault();

    try {
        const assetData = {
            name: document.getElementById('editAssetName').value,
            description: document.getElementById('editAssetDescription').value || ''
        };

        const assetId = document.getElementById('editAssetId').value;
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
            throw new Error(errorData.message || 'Failed to update asset');
        }

        showNotification('Asset updated successfully', 'success');
        closeAssetEditModal();
        loadAssets();
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
};





