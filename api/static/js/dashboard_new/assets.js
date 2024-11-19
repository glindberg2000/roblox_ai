import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

export async function loadAssets() {
    if (!state.currentGame) {
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading assets for game', {
            gameId: state.currentGame.id,
            gameSlug: state.currentGame.slug
        });

        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}`);
        const data = await response.json();
        state.currentAssets = data.assets;
        debugLog('Loaded Assets', state.currentAssets);

        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '';

        if (!state.currentAssets || state.currentAssets.length === 0) {
            assetList.innerHTML = '<p class="text-gray-400 text-center p-4">No assets found for this game</p>';
            return;
        }

        state.currentAssets.forEach(asset => {
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
                    <button onclick="window.editAsset('${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="window.deleteAsset('${asset.assetId}')" 
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

export async function editAsset(assetId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const asset = state.currentAssets.find(a => a.assetId === assetId);
    if (!asset) {
        showNotification('Asset not found', 'error');
        return;
    }

    console.log('Editing asset:', asset); // Debug log

    const modalContent = document.createElement('div');
    modalContent.className = 'p-6';
    modalContent.innerHTML = `
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-blue-400">Edit Asset</h2>
        </div>
        <form class="space-y-4">
            <input type="hidden" name="assetId" value="${asset.assetId}">
            
            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                <input type="text" name="name" value="${escapeHTML(asset.name)}" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
            </div>

            <div>
                <div class="flex items-center space-x-2 mb-1">
                    <label class="block text-sm font-medium text-gray-300">Current Image:</label>
                    <span class="text-sm text-gray-400">${asset.assetId}</span>
                </div>
                <img src="${asset.imageUrl}" alt="${escapeHTML(asset.name)}"
                    class="w-full h-48 object-contain rounded-lg border border-dark-600 bg-dark-700 mb-4">
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                <textarea name="description" required rows="4"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${escapeHTML(asset.description || '')}</textarea>
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
        
        // Get form values using form.elements
        const name = form.elements['name'].value.trim();
        const description = form.elements['description'].value.trim();

        console.log('Form values:', { name, description }); // Debug log

        // Validate
        if (!name) {
            showNotification('Name is required', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/games/${state.currentGame.id}/assets/${asset.assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description })
            });

            if (!response.ok) {
                throw new Error('Failed to update asset');
            }

            hideModal();
            showNotification('Asset updated successfully', 'success');
            loadAssets();  // Refresh the list
        } catch (error) {
            console.error('Error saving asset:', error);
            showNotification('Failed to save changes', 'error');
        }
    };
}

export async function saveAssetEdit(assetId) {
    try {
        // Get form values using the form element
        const form = document.getElementById('editAssetForm');
        const name = form.querySelector('#editAssetName').value.trim();
        const description = form.querySelector('#editAssetDescription').value.trim();

        // Debug log
        console.log('Saving asset with data:', { name, description });

        // Validate
        if (!name) {
            throw new Error('Name is required');
        }

        // Get the original asset to preserve existing data
        const asset = state.currentAssets.find(a => a.assetId === assetId);
        if (!asset) {
            throw new Error('Asset not found');
        }

        // Merge new data with existing data
        const data = {
            name: name || asset.name,
            description: description || asset.description,
            type: asset.type,  // Preserve existing type
            imageUrl: asset.imageUrl  // Preserve existing image URL
        };

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

        const result = await response.json();
        console.log('Asset updated:', result);

        hideModal();
        showNotification('Asset updated successfully', 'success');
        loadAssets();  // Refresh the list
    } catch (error) {
        console.error('Error saving asset:', error);
        showNotification(error.message, 'error');
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