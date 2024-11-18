// Centralized state management
export const state = {
    currentGame: null,
    currentTab: 'games',
    currentAssets: [],
    currentNPCs: []
};

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