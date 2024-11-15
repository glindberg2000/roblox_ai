class GamesDashboard {
    constructor() {
        console.log('GamesDashboard constructor called');
        this.gamesContainer = document.getElementById('games-container');
        this.gameSelector = document.getElementById('gameSelector');
        this.gameForm = document.getElementById('gameForm');
        console.log('Game selector element:', this.gameSelector);
        this.currentGameId = null;
        this.loadGames();
        this.bindEvents();
    }

    bindEvents() {
        // Bind the form submission
        if (this.gameForm) {
            console.log('Binding form submit event');
            this.gameForm.addEventListener('submit', (event) => {
                event.preventDefault();
                this.createGame(event);
            });
        } else {
            console.error('Game form not found');
        }
    }

    async createGame(event) {
        const form = event.target;
        const formData = new FormData(form);
        
        try {
            console.log('Creating new game...');
            const response = await fetch('/api/games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: formData.get('title'),
                    description: formData.get('description')
                })
            });
            
            if (!response.ok) throw new Error('Failed to create game');
            
            const result = await response.json();
            console.log('Game created:', result);
            
            // Clear form
            form.reset();
            
            // Refresh games list
            await this.loadGames();
            
            // Show success message
            alert('Game created successfully!');
        } catch (error) {
            console.error('Error creating game:', error);
            alert('Failed to create game. Please try again.');
        }
    }

    async loadGames() {
        try {
            console.log('Loading games...');
            const response = await fetch('/api/games');
            const games = await response.json();
            console.log('Raw games response:', games);
            
            if (!Array.isArray(games)) {
                console.error('Games response is not an array:', games);
                return;
            }
            
            console.log('Found', games.length, 'games');
            this.renderGames(games);
            this.updateGameSelector(games);
        } catch (error) {
            console.error('Failed to load games:', error);
        }
    }

    updateGameSelector(games) {
        console.log('Updating game selector with games:', games);
        if (!this.gameSelector) {
            console.error('Game selector element not found!');
            return;
        }
        
        const options = games.map(game => `
            <option value="${game.id}" ${game.id === this.currentGameId ? 'selected' : ''}>
                ${game.title}
            </option>
        `).join('');
        
        console.log('Generated options:', options);
        
        this.gameSelector.innerHTML = `
            <option value="">Select a game...</option>
            ${options}
        `;
        console.log('Updated game selector HTML:', this.gameSelector.innerHTML);
    }

    renderGames(games) {
        console.log('Rendering games:', games);
        if (!this.gamesContainer) {
            console.error('Games container element not found!');
            return;
        }
        
        const html = games.map(game => `
            <div class="bg-dark-800 p-6 rounded-xl shadow-xl">
                <h3 class="text-xl font-bold mb-2 text-blue-400">${game.title}</h3>
                <p class="text-gray-300 mb-4">${game.description || 'No description'}</p>
                <div class="flex space-x-4 text-gray-400 mb-4">
                    <span><i class="fas fa-cube"></i> Assets: ${game.asset_count}</span>
                    <span><i class="fas fa-user"></i> NPCs: ${game.npc_count}</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="gamesDashboard.editGame('${game.slug}')"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="gamesDashboard.deleteGame('${game.slug}')"
                        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
        
        console.log('Generated HTML:', html);
        this.gamesContainer.innerHTML = html;
    }

    async editGame(slug) {
        try {
            // Fetch the game data
            const response = await fetch(`/api/games/${slug}`);
            const game = await response.json();
            
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.style.display = 'block';
            modal.innerHTML = `
                <div class="modal-content">
                    <h2 class="text-xl font-bold mb-4 text-blue-400">Edit Game</h2>
                    <form id="edit-game-form" class="space-y-4">
                        <input type="hidden" id="edit-game-slug" value="${slug}">
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
                        <div class="flex justify-end space-x-4">
                            <button type="button" onclick="this.closest('.modal').remove()"
                                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">Cancel</button>
                            <button type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Save Changes</button>
                        </div>
                    </form>
                </div>
            `;

            document.body.appendChild(modal);

            document.getElementById('edit-game-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const slug = document.getElementById('edit-game-slug').value;
                const title = document.getElementById('edit-game-title').value;
                const description = document.getElementById('edit-game-description').value;

                try {
                    const response = await fetch(`/api/games/${slug}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ title, description })
                    });

                    if (!response.ok) throw new Error('Failed to update game');
                    
                    await this.loadGames();
                    modal.remove();
                } catch (error) {
                    console.error('Error updating game:', error);
                    alert('Failed to update game. Please try again.');
                }
            });
        } catch (error) {
            console.error('Error editing game:', error);
            alert('Failed to edit game. Please try again.');
        }
    }

    async deleteGame(slug) {
        if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/games/${slug}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete game');
            
            await this.loadGames();
            alert('Game deleted successfully');
        } catch (error) {
            console.error('Error deleting game:', error);
            alert('Failed to delete game. Please try again.');
        }
    }

    async switchGame(gameId) {
        this.currentGameId = gameId;
        if (gameId) {
            // Store selected game ID in localStorage
            localStorage.setItem('currentGameId', gameId);
            
            // Reload assets and NPCs for the selected game
            try {
                // Clear existing lists
                document.getElementById('assetList').innerHTML = '';
                document.getElementById('npcList').innerHTML = '';
                
                // Load assets for selected game
                const assetsResponse = await fetch(`/api/assets?game_id=${gameId}`);
                const assets = await assetsResponse.json();
                renderAssetList(assets);

                // Load NPCs for selected game
                const npcsResponse = await fetch(`/api/npcs?game_id=${gameId}`);
                const npcs = await npcsResponse.json();
                renderNPCList(npcs);
            } catch (error) {
                console.error('Error loading game data:', error);
            }
        } else {
            localStorage.removeItem('currentGameId');
            // Clear lists when no game is selected
            document.getElementById('assetList').innerHTML = '';
            document.getElementById('npcList').innerHTML = '';
        }
    }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing GamesDashboard');
    window.gamesDashboard = new GamesDashboard();
}); 