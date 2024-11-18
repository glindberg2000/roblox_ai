import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentGame } from './state.js';

// Export game-related functions
export async function loadGames() {
    console.log('Loading games...');
    try {
        const response = await fetch('/api/games');
        const games = await response.json();
        console.log('Loaded games:', games);

        const gamesContainer = document.getElementById('games-container');
        if (!gamesContainer) {
            console.error('games-container element not found!');
            return;
        }

        gamesContainer.innerHTML = '';

        games.forEach(game => {
            console.log('Creating card for game:', game);
            const gameCard = document.createElement('div');
            gameCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            gameCard.innerHTML = `
                <h3 class="text-xl font-bold text-gray-100 mb-2">${game.title}</h3>
                <p class="text-gray-400 mb-4">${game.description || 'No description'}</p>
                <div class="flex items-center text-sm text-gray-400 mb-4">
                    <span class="mr-4"><i class="fas fa-cube"></i> Assets: ${game.asset_count || 0}</span>
                    <span><i class="fas fa-user"></i> NPCs: ${game.npc_count || 0}</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="window.selectGame('${game.slug}')" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200">
                        <i class="fas fa-check-circle"></i> Select
                    </button>
                    <button onclick="window.editGame('${game.slug}')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="window.deleteGame('${game.slug}')" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `;
            gamesContainer.appendChild(gameCard);
            console.log('Added game card:', game.title);
        });
    } catch (error) {
        console.error('Error loading games:', error);
        showNotification('Failed to load games', 'error');
    }
}

export async function selectGame(gameSlug) {
    try {
        debugLog('Selecting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`);

        if (!response.ok) {
            throw new Error(`Failed to select game: ${response.statusText}`);
        }

        const game = await response.json();
        updateCurrentGame(game);  // Use state management function
        console.log('Game selected:', game);

        showNotification(`Selected game: ${game.title}`, 'success');

        // Stay on current tab and refresh data
        if (state.currentTab === 'assets') {
            window.loadAssets();
        } else if (state.currentTab === 'npcs') {
            window.loadNPCs();
        }

    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification(`Failed to select game: ${error.message}`, 'error');
    }
}

export async function editGame(gameSlug) {
    try {
        debugLog('Editing game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`);
        const game = await response.json();

        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Game</h2>
            </div>
            <form id="edit-game-form" class="space-y-4">
                <input type="hidden" id="edit-game-slug" value="${gameSlug}">
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Title</label>
                    <input type="text" id="edit-game-title" value="${game.title}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description</label>
                    <textarea id="edit-game-description" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
                </div>
            </form>
        `;

        showModal(modalContent);

        // Add form submit handler
        const form = modalContent.querySelector('form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            await saveGameEdit(gameSlug);
        };

    } catch (error) {
        console.error('Error editing game:', error);
        showNotification('Failed to edit game', 'error');
    }
}

export async function saveGameEdit(gameSlug) {
    try {
        const title = document.getElementById('edit-game-title').value;
        const description = document.getElementById('edit-game-description').value;

        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description })
        });

        if (!response.ok) {
            throw new Error('Failed to update game');
        }

        hideModal();
        showNotification('Game updated successfully', 'success');
        loadGames();
    } catch (error) {
        console.error('Error saving game:', error);
        showNotification('Failed to save changes', 'error');
    }
}

export async function deleteGame(gameSlug) {
    if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
        return;
    }

    try {
        debugLog('Deleting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete game');
        }

        showNotification('Game deleted successfully', 'success');
        loadGames();
    } catch (error) {
        console.error('Error deleting game:', error);
        showNotification('Failed to delete game', 'error');
    }
}

// Make functions globally available
window.loadGames = loadGames;
window.selectGame = selectGame;
window.editGame = editGame;
window.deleteGame = deleteGame; 