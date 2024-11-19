import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';

console.log('Loading NEW dashboard version');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing dashboard...');
    await loadGames();
});

// Add populateAssetSelector function
async function populateAssetSelector() {
    if (!state.currentGame) {
        console.log('No game selected for asset selector');
        return;
    }

    try {
        // Fetch only NPC type assets
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        
        const assetSelect = document.getElementById('editNpcModel');
        if (assetSelect) {
            // Clear existing options
            assetSelect.innerHTML = '<option value="">Select a model...</option>';
            
            // Add options for each asset
            if (data.assets && Array.isArray(data.assets)) {
                data.assets.forEach(asset => {
                    const option = document.createElement('option');
                    option.value = asset.assetId;
                    option.textContent = asset.name;
                    assetSelect.appendChild(option);
                });
            }
            console.log('Populated model selector with', data.assets?.length || 0, 'assets');
        }
    } catch (error) {
        console.error('Error loading models for selector:', error);
        showNotification('Failed to load models for selection', 'error');
    }
}

// Tab management
window.showTab = function(tabName) {
    console.log('Showing tab:', tabName);
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    updateCurrentTab(tabName);

    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        window.loadNPCs();
        populateAssetSelector();
    }
};

// Make populateAssetSelector globally available
window.populateAssetSelector = populateAssetSelector;

async function createGame(title, description, cloneFrom = null) {
    try {
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                description,
                cloneFrom
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Game created:', data);
        
        // Redirect to the game's page
        window.location.href = `/dashboard?game=${data.slug}`;
    } catch (error) {
        console.error('Error creating game:', error);
        alert('Failed to create game: ' + error.message);
    }
}

// Add event listener to form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#createGameForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const title = document.querySelector('#gameTitle').value;
            const description = document.querySelector('#gameDescription').value;
            const cloneFrom = document.querySelector('#cloneFrom')?.value;
            
            await createGame(title, description, cloneFrom);
        });
    }
});

// Handle game form submission
window.handleGameSubmit = async function(event) {
    event.preventDefault();
    
    const form = event.target;
    const title = form.querySelector('[name="title"]').value;
    const description = form.querySelector('[name="description"]').value;
    const cloneFrom = form.querySelector('[name="cloneFrom"]').value;

    try {
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                description,
                cloneFrom: cloneFrom || null
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Game created:', result);
        
        // Refresh the games list
        await loadGames();
        
        // Clear the form
        form.reset();
        
        // Show success message
        showNotification('Game created successfully!', 'success');
        
    } catch (error) {
        console.error('Error creating game:', error);
        showNotification('Failed to create game: ' + error.message, 'error');
    }
}







