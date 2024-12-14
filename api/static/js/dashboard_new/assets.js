import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

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
                const assetCard = document.createElement('div');
                assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
                
                // Create the card content without onclick string attributes
                assetCard.innerHTML = `
                    <div class="aspect-w-16 aspect-h-9 mb-4">
                        <img src="${asset.imageUrl || ''}" 
                             alt="${asset.name}" 
                             class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                    </div>
                    <h3 class="font-bold text-lg mb-2 text-gray-100">${asset.name}</h3>
                    <p class="text-sm text-gray-400 mb-2">ID: ${asset.assetId}</p>
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

                // Add event listeners properly
                const editBtn = assetCard.querySelector('.edit-asset-btn');
                const deleteBtn = assetCard.querySelector('.delete-asset-btn');
                
                editBtn.addEventListener('click', () => editAsset(asset.assetId));
                deleteBtn.addEventListener('click', () => deleteAsset(asset.assetId));
                
                assetList.appendChild(assetCard);
            });
        } else {
            assetList.innerHTML = '<p class="text-gray-400">No assets found</p>';
        }
        
        // Update game ID in asset form
        const gameIdInput = document.getElementById('assetFormGameId');
        if (gameIdInput) {
            gameIdInput.value = state.currentGame.id;
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
        const asset = data.assets.find(a => a.assetId === assetId);

        if (!asset) {
            showNotification('Asset not found', 'error');
            return;
        }

        // Get the modal and form elements
        const modal = document.getElementById('assetEditModal');
        const form = document.getElementById('assetEditForm');
        const nameInput = form.querySelector('#editAssetName');
        const descriptionInput = form.querySelector('#editAssetDescription');
        const assetIdInput = form.querySelector('#editAssetId');
        const imageElement = form.querySelector('#editAssetImage');
        const assetIdDisplay = form.querySelector('#editAssetId_display');

        // Populate the form
        nameInput.value = asset.name;
        descriptionInput.value = asset.description || '';
        assetIdInput.value = asset.assetId;
        imageElement.src = asset.imageUrl || '';
        assetIdDisplay.textContent = asset.assetId;

        // Show the modal
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
    
    const form = event.target;
    const assetId = form.querySelector('#editAssetId').value;
    const name = form.querySelector('#editAssetName').value.trim();
    const description = form.querySelector('#editAssetDescription').value.trim();

    try {
        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) {
            throw new Error('Failed to update asset');
        }

        closeAssetEditModal();
        showNotification('Asset updated successfully', 'success');
        loadAssets();
    } catch (error) {
        console.error('Error saving asset:', error);
        showNotification('Failed to save changes', 'error');
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