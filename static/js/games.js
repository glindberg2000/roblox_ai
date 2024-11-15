class GamesDashboard {
    constructor() {
        this.gamesContainer = document.getElementById('games-container');
        this.gameSelector = document.getElementById('gameSelector');
        this.currentGameId = localStorage.getItem('currentGameId');
        this.currentGameTitle = '';
        this.loadGames();
        this.updateFormsState();
    }

    updateFormsState() {
        const assetForm = document.getElementById('assetForm');
        const npcForm = document.getElementById('npcForm');
        const message = 'Please select a game before creating assets or NPCs';

        if (!this.currentGameId) {
            if (assetForm) {
                assetForm.classList.add('disabled');
                assetForm.querySelector('button[type="submit"]').disabled = true;
                assetForm.insertAdjacentHTML('beforebegin', 
                    `<div class="text-red-500 mb-4">${message}</div>`);
            }
            if (npcForm) {
                npcForm.classList.add('disabled');
                npcForm.querySelector('button[type="submit"]').disabled = true;
                npcForm.insertAdjacentHTML('beforebegin', 
                    `<div class="text-red-500 mb-4">${message}</div>`);
            }
        } else {
            if (assetForm) {
                assetForm.classList.remove('disabled');
                assetForm.querySelector('button[type="submit"]').disabled = false;
                const warning = assetForm.previousElementSibling;
                if (warning && warning.textContent === message) warning.remove();
            }
            if (npcForm) {
                npcForm.classList.remove('disabled');
                npcForm.querySelector('button[type="submit"]').disabled = false;
                const warning = npcForm.previousElementSibling;
                if (warning && warning.textContent === message) warning.remove();
            }
        }
    }

    async createGame(event) {
        event.preventDefault();
        const form = event.target;
        const title = form.title.value;
        const description = form.description.value;
        
        try {
            const response = await fetch('/api/games', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title, description })
            });
            
            if (!response.ok) throw new Error('Failed to create game');
            
            // Clear form
            form.reset();
            
            // Refresh games list
            await this.loadGames();
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
            console.log('Loaded games:', games);
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
        
        this.gameSelector.innerHTML = `
            <option value="">Select a game...</option>
            ${games.map(game => `
                <option value="${game.id}" ${game.id === this.currentGameId ? 'selected' : ''}>
                    ${game.title}
                </option>
            `).join('')}
        `;
        console.log('Game selector updated:', this.gameSelector.innerHTML);
    }

    async switchGame(gameId) {
        console.log('Switching to game:', gameId);
        
        try {
            this.currentGameId = gameId;
            
            if (gameId) {
                const response = await fetch(`/api/games/${gameId}`);
                const gameData = await response.json();
                this.currentGameTitle = gameData.title;
                localStorage.setItem('currentGameId', gameId);
            } else {
                this.currentGameTitle = '';
                localStorage.removeItem('currentGameId');
            }

            this.updateGameContext();
            this.updateFormsState();
            await this.reloadAssetsAndNPCs(gameId);
            
        } catch (error) {
            console.error('Error switching game:', error);
            alert('Failed to switch game. Please try again.');
        }
    }

    async reloadAssetsAndNPCs(gameId) {
        // Reload assets
        const assetsResponse = await fetch(`/api/assets?game_id=${gameId}`);
        const assets = await assetsResponse.json();
        renderAssetList(assets); // This function should exist in your dashboard.js

        // Reload NPCs
        const npcsResponse = await fetch(`/api/npcs?game_id=${gameId}`);
        const npcs = await npcsResponse.json();
        renderNPCList(npcs); // This function should exist in your dashboard.js
    }

    renderGames(games) {
        this.gamesContainer.innerHTML = games.map(game => `
            <div class="bg-dark-800 p-6 rounded-xl shadow-xl">
                <h3 class="text-xl font-bold mb-2 text-blue-400">${game.title}</h3>
                <p class="text-gray-300 mb-4">${game.description}</p>
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
    }

    async editGame(slug) {
        // TODO: Implement edit functionality
        console.log('Edit game:', slug);
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
            
            await this.loadGames(); // Refresh the games list
        } catch (error) {
            console.error('Error deleting game:', error);
            alert('Failed to delete game. Please try again.');
        }
    }

    async selectGame(slug) {
        try {
            const response = await fetch(`/api/games/${slug}`);
            this.currentGame = await response.json();
            this.renderCurrentGame();
        } catch (error) {
            console.error('Failed to select game:', error);
        }
    }

    renderCurrentGame() {
        if (!this.currentGame) {
            this.currentGameContainer.innerHTML = `
                <p class="text-gray-400">No game selected</p>
            `;
            return;
        }

        this.currentGameContainer.innerHTML = `
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="text-lg font-bold text-blue-400">${this.currentGame.title}</h4>
                    <p class="text-gray-400 mt-2">${this.currentGame.description}</p>
                    <div class="flex space-x-4 mt-2 text-sm text-gray-500">
                        <span>Assets: ${this.currentGame.asset_count}</span>
                        <span>NPCs: ${this.currentGame.npc_count}</span>
                    </div>
                </div>
                <button onclick="gamesDashboard.editCurrentGame()"
                    class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors duration-200">
                    Edit
                </button>
            </div>
        `;
    }

    async editCurrentGame() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        modal.innerHTML = `
            <div class="modal-content">
                <h2 class="text-xl font-bold mb-4 text-blue-400">Edit Game</h2>
                <form id="edit-game-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Title</label>
                        <input type="text" id="edit-game-title" value="${this.currentGame.title}" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Description</label>
                        <textarea id="edit-game-description" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${this.currentGame.description}</textarea>
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
            await this.updateCurrentGame();
            modal.remove();
        });
    }

    async updateCurrentGame() {
        const title = document.getElementById('edit-game-title').value;
        const description = document.getElementById('edit-game-description').value;

        try {
            const response = await fetch(`/api/games/${this.currentGame.slug}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title, description })
            });

            if (!response.ok) throw new Error('Failed to update game');

            await this.loadGames();
        } catch (error) {
            console.error('Error updating game:', error);
            alert('Failed to update game. Please try again.');
        }
    }
}

window.gamesDashboard = new GamesDashboard(); 