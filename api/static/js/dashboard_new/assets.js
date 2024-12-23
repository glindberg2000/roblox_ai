import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

// Add at the top of the file with other constants
const AREA_DISPLAY_NAMES = {
    'spawn_area': 'Spawn Area',
    'market_district': 'Market District',
    'town_center': 'Town Center',
    'residential': 'Residential Area'
};

export async function loadAssets() {
    if (!state.currentGame) {
        console.warn('No game selected');
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}`);
        const data = await response.json();

        const assetList = document.getElementById('assetList');
        if (!assetList) return;

        assetList.innerHTML = '';

        if (data.assets && data.assets.length > 0) {
            data.assets.forEach(asset => {
                try {
                    const assetCard = document.createElement('div');
                    assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';

                    // Safely parse JSON fields
                    let aliases = [];
                    if (asset.aliases) {
                        try {
                            aliases = typeof asset.aliases === 'string' ?
                                JSON.parse(asset.aliases) : asset.aliases;
                        } catch (e) {
                            console.warn('Failed to parse aliases:', e);
                        }
                    }

                    let locationData = {};
                    if (asset.location_data) {
                        try {
                            locationData = typeof asset.location_data === 'string' ?
                                JSON.parse(asset.location_data) : asset.location_data;
                        } catch (e) {
                            console.warn('Failed to parse location_data:', e);
                        }
                    }

                    // Create the card content
                    assetCard.innerHTML = `
                        <div class="aspect-w-16 aspect-h-9 mb-4">
                            <img src="${asset.image_url || ''}" 
                                 alt="${asset.name}" 
                                 class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                        </div>
                        <h3 class="font-bold text-lg mb-2 text-gray-100">${asset.name}</h3>
                        <p class="text-sm text-gray-400 mb-2">ID: ${asset.asset_id}</p>
                        <p class="text-sm text-gray-400 mb-2">Type: ${asset.type || 'Unknown'}</p>
                        ${asset.is_location ? `
                            <div class="text-sm text-gray-400 mb-2">
                                <p>Location: (${asset.position_x || '?'}, ${asset.position_y || '?'}, ${asset.position_z || '?'})</p>
                                <p>Area: ${getAreaDisplayName(locationData.area) || 'Unknown'}</p>
                                ${aliases.length > 0 ? `
                                    <p>Aliases: ${aliases.join(', ')}</p>
                                ` : ''}
                            </div>
                        ` : ''}
                        <p class="text-sm text-gray-400 mb-4">${asset.description || 'No description'}</p>
                        <div class="flex space-x-2">
                            <button class="edit-asset-btn flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Edit
                            </button>
                            <button class="delete-asset-btn flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                                Delete
                            </button>
                        </div>
                    `;

                    // Add event listeners
                    const editBtn = assetCard.querySelector('.edit-asset-btn');
                    const deleteBtn = assetCard.querySelector('.delete-asset-btn');

                    editBtn.addEventListener('click', () => editAsset(asset.asset_id));
                    deleteBtn.addEventListener('click', () => deleteAsset(asset.asset_id));

                    assetList.appendChild(assetCard);
                } catch (cardError) {
                    console.error('Error creating asset card:', cardError, asset);
                }
            });
        } else {
            assetList.innerHTML = '<p class="text-gray-400">No assets found</p>';
        }

    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
    }
}

export async function editAsset(assetId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}`);
        const data = await response.json();
        const asset = data.assets.find(a => a.asset_id === assetId);

        if (!asset) {
            showNotification('Asset not found', 'error');
            return;
        }

        // Get all form elements
        const form = document.getElementById('assetEditForm');
        const nameInput = document.getElementById('editAssetName');
        const typeInput = document.getElementById('editAssetType');
        const descriptionInput = document.getElementById('editAssetDescription');
        const assetIdInput = document.getElementById('editAssetId');
        const isLocationInput = document.getElementById('editAssetIsLocation');
        const locationFields = document.getElementById('editLocationFields');

        // Populate basic fields
        nameInput.value = asset.name;
        typeInput.value = asset.type || 'Model';
        descriptionInput.value = asset.description || '';
        assetIdInput.value = asset.asset_id;

        // Handle location fields
        isLocationInput.checked = asset.is_location;
        locationFields.style.display = asset.is_location ? 'block' : 'none';

        if (asset.is_location) {
            // Set position values
            document.getElementById('editPositionX').value = asset.position_x || '';
            document.getElementById('editPositionY').value = asset.position_y || '';
            document.getElementById('editPositionZ').value = asset.position_z || '';

            const locationData = typeof asset.location_data === 'string' ?
                JSON.parse(asset.location_data) : asset.location_data || {};

            document.getElementById('editLocationArea').value = locationData.area || 'spawn_area';
            document.getElementById('editLocationType').value = locationData.type || 'shop';
            document.getElementById('editLocationOwner').value = locationData.owner || '';
            document.getElementById('editLocationInteractable').checked = locationData.interactable || false;
            document.getElementById('editLocationTags').value = (locationData.tags || []).join(', ');
        }

        // Show the modal
        const modal = document.getElementById('assetEditModal');
        modal.style.display = 'block';

    } catch (error) {
        console.error('Error editing asset:', error);
        showNotification('Failed to load asset data', 'error');
    }
}

export function closeAssetEditModal() {
    const modal = document.getElementById('assetEditModal');
    modal.style.display = 'none';
}

export async function saveAssetEdit(event) {
    event.preventDefault();

    try {
        const assetId = document.getElementById('editAssetId').value;
        const isLocation = document.getElementById('editAssetIsLocation').checked;

        // Build update data
        const data = {
            name: document.getElementById('editAssetName').value,
            type: document.getElementById('editAssetType').value,
            description: document.getElementById('editAssetDescription').value,
            is_location: isLocation
        };

        // Add location data if is_location is true
        if (isLocation) {
            // Add position data
            data.position_x = parseFloat(document.getElementById('editPositionX').value) || null;
            data.position_y = parseFloat(document.getElementById('editPositionY').value) || null;
            data.position_z = parseFloat(document.getElementById('editPositionZ').value) || null;

            // Add aliases
            data.aliases = document.getElementById('editAliases').value
                .split(',')
                .map(a => a.trim())
                .filter(a => a.length > 0);

            const areaSelect = document.getElementById('editLocationArea');
            const areaValue = areaSelect.value === 'other'
                ? document.getElementById('editLocationAreaCustom').value
                : areaSelect.value;

            data.location_data = {
                area: areaValue,
                type: document.getElementById('editLocationType').value,
                owner: document.getElementById('editLocationOwner').value,
                interactable: document.getElementById('editLocationInteractable').checked,
                tags: document.getElementById('editLocationTags').value
                    .split(',')
                    .map(t => t.trim())
                    .filter(t => t.length > 0)
            };
        }

        console.log('Sending update with data:', data);

        // Send update request
        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update asset');
        }

        // Refresh asset list
        await loadAssets();

        // Close modal
        closeAssetEditModal();

    } catch (error) {
        console.error('Error updating asset:', error);
        alert('Failed to update asset');
    }
}

export async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }

    try {
        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete asset');
        }

        showNotification('Asset deleted successfully', 'success');
        loadAssets();
    } catch (error) {
        console.error('Error deleting asset:', error);
        showNotification('Failed to delete asset', 'error');
    }
}

export async function createAsset(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const submitBtn = document.getElementById('submitAssetBtn');
    submitBtn.disabled = true;

    try {
        const formData = new FormData(event.target);
        formData.set('game_id', state.currentGame.id);

        debugLog('Submitting asset form with data:', {
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
        event.target.reset();
        loadAssets();

    } catch (error) {
        console.error('Error creating asset:', error);
        showNotification(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
    }
}

// Make functions globally available
window.loadAssets = loadAssets;
window.editAsset = editAsset;
window.deleteAsset = deleteAsset;
window.createAsset = createAsset;
window.closeAssetEditModal = closeAssetEditModal;
window.saveAssetEdit = saveAssetEdit;

// Helper function to escape HTML
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, (tag) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag]));
}

function insertLocationTemplate() {
    const template = {
        area: "spawn_area",
        type: "shop",
        owner: "",
        interactable: true,
        tags: []
    };

    document.getElementById('editLocationData').value =
        JSON.stringify(template, null, 2);
}

// Add to window exports
window.insertLocationTemplate = insertLocationTemplate;

function toggleCustomArea() {
    const areaSelect = document.getElementById('editLocationArea');
    const customInput = document.getElementById('editLocationAreaCustom');
    customInput.style.display = areaSelect.value === 'other' ? 'block' : 'none';
}

window.toggleCustomArea = toggleCustomArea;

// Helper function to get display name
function getAreaDisplayName(areaSlug) {
    return AREA_DISPLAY_NAMES[areaSlug] || areaSlug;
} 