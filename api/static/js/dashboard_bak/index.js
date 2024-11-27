// Import modules
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import * as npc from './npc.js';

// Shared state
export let currentGame = null;
export let currentTab = 'games';
export let currentAssets = [];
export let currentNPCs = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing dashboard...');
    showTab('games');
    loadGames();
});

// Tab management
export function showTab(tabName) {
    debugLog('Showing tab:', { tabName });
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    currentTab = tabName;

    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && currentGame) {
        loadAssets();
    } else if (tabName === 'npcs' && currentGame) {
        loadNPCs();
        populateAssetSelector();
    }
}

// Data loading functions
export async function loadAssets() {
    if (!currentGame) {
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${currentGame.id}`);
        const data = await response.json();
        currentAssets = data.assets;
        // ... rest of loadAssets function
    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
    }
}

export async function loadNPCs() {
    if (!currentGame) {
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        const response = await fetch(`/api/npcs?game_id=${currentGame.id}`);
        const data = await response.json();
        currentNPCs = data.npcs;
        // ... rest of loadNPCs function
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
    }
}

// Make functions globally available
window.showTab = showTab;
window.loadAssets = loadAssets;
window.loadNPCs = loadNPCs;
