import { state, updateNavigationState } from './state.js';
import { showNotification } from './ui.js';

export async function selectGame(gameId) {
    try {
        const response = await fetch(`/api/games/${gameId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch game data');
        }
        
        const gameData = await response.json();
        
        // Update state and navigation
        state.currentGame = gameData;
        updateNavigationState();
        
        // Update display
        const display = document.getElementById('currentGameDisplay');
        if (display) {
            display.textContent = `Current Game: ${gameData.title}`;
        }
        
        showNotification('Game selected successfully', 'success');
        
    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification('Failed to select game', 'error');
    }
}

// Make function globally available
window.selectGame = selectGame; 