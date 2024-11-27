import { currentGame, loadAssets, loadNPCs } from './index.js';

export async function selectGame(gameSlug) {
    try {
        const response = await fetch(`/api/games/${gameSlug}`);
        if (!response.ok) {
            throw new Error(`Failed to select game: ${response.statusText}`);
        }

        const game = await response.json();
        currentGame = game;

        // Update display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${game.title}`;
        }

        // Reload current tab data
        if (currentTab === 'assets') {
            loadAssets();
        } else if (currentTab === 'npcs') {
            loadNPCs();
        }

        showNotification(`Selected game: ${game.title}`, 'success');

    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification(`Failed to select game: ${error.message}`, 'error');
    }
}
