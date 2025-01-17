import { state, updateNavigationState } from './state.js';
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { switchTab } from './index.js';

export async function loadGames() {
    try {
        const response = await fetch('/api/games');
        const games = await response.json();
        
        const container = document.getElementById('games-container');
        if (!container) return;
        
        container.innerHTML = '';
        games.forEach(game => {
            const gameCard = createGameCard(game);
            container.appendChild(gameCard);
        });
        
        // Also populate clone selector
        populateCloneSelector(games);
        
    } catch (error) {
        console.error('Error loading games:', error);
        showNotification('Failed to load games', 'error');
    }
}

function createGameCard(game) {
    const card = document.createElement('div');
    card.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
    
    card.innerHTML = `
        <h3 class="font-bold text-lg mb-2 text-gray-100">${game.title}</h3>
        <p class="text-sm text-gray-400 mb-4">${game.description || 'No description'}</p>
        <div class="text-sm text-gray-400 mb-4">
            <div>Assets: ${game.asset_count || 0}</div>
            <div>NPCs: ${game.npc_count || 0}</div>
        </div>
        <div class="flex space-x-2">
            <button onclick="selectGame('${game.slug}')" 
                    class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Select
            </button>
            <button onclick="editGame('${game.slug}')"
                    class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                Edit
            </button>
            <button onclick="deleteGame('${game.slug}')"
                    class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                Delete
            </button>
        </div>
    `;
    
    return card;
}

export async function selectGame(gameSlug) {
    debugLog('Selecting game', { gameSlug });
    
    try {
        const response = await fetch(`/api/games/${gameSlug}`);
        if (!response.ok) {
            throw new Error('Failed to fetch game data');
        }
        
        const gameData = await response.json();
        console.log('Game selected:', gameData);
        
        // Update state
        state.currentGame = gameData;
        updateNavigationState();
        
        // Update display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${gameData.title}`;
        }
        
        // Load initial data without forcing tab switch
        if (window.loadAssets) {
            await window.loadAssets();
        }
        if (window.loadNPCs) {
            await window.loadNPCs();
        }
        
        showNotification('Game selected successfully', 'success');
        
    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification('Failed to select game', 'error');
    }
}

// Add game creation function
export async function handleGameSubmit(event) {
    event.preventDefault();
    
    try {
        const form = event.target;
        const formData = new FormData(form);
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            cloneFrom: formData.get('cloneFrom')
        };
        
        debugLog('Creating game with data:', data);
        
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create game');
        }

        const result = await response.json();
        showNotification('Game created successfully', 'success');
        form.reset();
        loadGames();  // Refresh the list
        
    } catch (error) {
        console.error('Error creating game:', error);
        showNotification(error.message, 'error');
    }
    
    return false;  // Prevent form submission
}

// Add game deletion function
export async function deleteGame(gameSlug) {
    if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete game');
        }

        showNotification('Game deleted successfully', 'success');
        loadGames();  // Refresh the list
        
        // If this was the current game, reset state
        if (state.currentGame && state.currentGame.slug === gameSlug) {
            state.currentGame = null;
            updateNavigationState();
            const display = document.getElementById('currentGameDisplay');
            if (display) {
                display.textContent = '';
            }
            switchTab('games');
        }
        
    } catch (error) {
        console.error('Error deleting game:', error);
        showNotification(error.message, 'error');
    }
}

// Add edit game function
export async function editGame(gameSlug) {
    try {
        const game = await fetch(`/api/games/${gameSlug}`).then(r => r.json());
        
        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Game</h2>
            </div>
            <form id="editGameForm" class="space-y-4">
                <input type="hidden" name="gameSlug" value="${game.slug}">
                
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Title:</label>
                    <input type="text" name="title" value="${game.title}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                    <textarea name="description" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
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
            
            const formData = new FormData(form);
            const data = {
                title: formData.get('title'),
                description: formData.get('description')
            };

            try {
                const response = await fetch(`/api/games/${game.slug}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    throw new Error('Failed to update game');
                }

                hideModal();
                showNotification('Game updated successfully', 'success');
                loadGames();
            } catch (error) {
                console.error('Error updating game:', error);
                showNotification(error.message, 'error');
            }
        };
    } catch (error) {
        console.error('Error editing game:', error);
        showNotification('Failed to load game data', 'error');
    }
}

// Make all functions globally available
window.selectGame = selectGame;
window.loadGames = loadGames;
window.handleGameSubmit = handleGameSubmit;
window.deleteGame = deleteGame;
window.populateCloneSelector = populateCloneSelector;
window.editGame = editGame;

// Add this function
function populateCloneSelector(games) {
    const selector = document.getElementById('cloneFromSelect');
    if (!selector) return;
    
    // Clear existing options except the default
    selector.innerHTML = '<option value="">Empty Game (No Assets)</option>';
    
    // Add games as options
    games.forEach(game => {
        const option = document.createElement('option');
        option.value = game.slug;
        option.textContent = game.title;
        selector.appendChild(option);
    });
} 