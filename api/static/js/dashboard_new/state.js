// Create singleton state
const state = {
    currentGame: null,
    currentSection: 'games',
    currentAssets: [],
    currentNPCs: []
};

// Export single instance
export { state };

// State update functions
export function updateCurrentGame(game) {
    state.currentGame = game;
    // Update UI
    const display = document.getElementById('currentGameDisplay');
    if (display) {
        display.textContent = `Current Game: ${game.title}`;
    }
}

export function updateCurrentTab(tab) {
    state.currentTab = tab;
}

export function updateCurrentAssets(assets) {
    state.currentAssets = assets;
}

export function updateCurrentNPCs(npcs) {
    state.currentNPCs = npcs;
}

export function resetState() {
    state.currentGame = null;
    state.currentAssets = [];
    state.currentNPCs = [];
}

// Add navigation state management
export function updateNavigationState() {
    const hasGame = !!state.currentGame;
    
    // Get nav buttons
    const assetNav = document.getElementById('nav-assets');
    const npcNav = document.getElementById('nav-npcs');
    const playerNav = document.getElementById('nav-players');
    
    // Update button states
    [assetNav, npcNav, playerNav].forEach(btn => {
        if (btn) {
            btn.disabled = !hasGame;
            // Update styles
            if (hasGame) {
                btn.classList.remove('text-gray-400');
                btn.classList.add('text-gray-100');
            } else {
                btn.classList.add('text-gray-400');
                btn.classList.remove('text-gray-100');
            }
        }
    });
}

// Update the setCurrentGame function
export function setCurrentGame(game) {
    state.currentGame = game;
    updateNavigationState();
    // ... rest of the existing function
} 