let currentGameId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize games dashboard
    if (window.gamesDashboard) {
        window.gamesDashboard.loadGames();
    }
    
    // Don't load assets/NPCs until a game is selected
    const currentGameId = localStorage.getItem('currentGameId');
    if (currentGameId) {
        loadAssetsAndNPCs(currentGameId);
    } else {
        // Clear lists if no game selected
        document.getElementById('assetList').innerHTML = '';
        document.getElementById('npcList').innerHTML = '';
    }
});

async function loadAssetsAndNPCs(gameId) {
    if (!gameId) {
        // Clear lists if no game selected
        document.getElementById('assetList').innerHTML = '';
        document.getElementById('npcList').innerHTML = '';
        return;
    }
    
    try {
        // Load assets for selected game
        const assetsResponse = await fetch(`/api/assets?game_id=${gameId}`);
        const assetsData = await assetsResponse.json();
        renderAssetList(assetsData);

        // Load NPCs for selected game
        const npcsResponse = await fetch(`/api/npcs?game_id=${gameId}`);
        const npcsData = await npcsResponse.json();
        renderNPCList(npcsData);
    } catch (error) {
        console.error('Error loading assets and NPCs:', error);
    }
}

function showTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        console.log('Found tab:', selectedTab);
        selectedTab.classList.remove('hidden');
        
        // If switching to games tab, refresh the games list
        if (tabName === 'games' && window.gamesDashboard) {
            console.log('Refreshing games list');
            window.gamesDashboard.loadGames();
        }
        // If switching to NPCs tab, load NPCs for current game
        else if (tabName === 'npcs') {
            loadNPCs();
        }
    } else {
        console.error('Tab not found:', tabName + 'Tab');
    }
}

async function loadNPCs() {
    const currentGameId = localStorage.getItem('currentGameId');
    if (!currentGameId) {
        document.getElementById('npcList').innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`/api/npcs?game_id=${currentGameId}`);
        const data = await response.json();
        renderNPCList(data);
    } catch (error) {
        console.error('Failed to load NPCs:', error);
    }
}

// Add these functions to handle NPC editing
async function editNPC(npcId) {
    try {
        const response = await fetch(`/api/npcs/${npcId}`);
        const npc = await response.json();
        
        // Populate the edit modal
        document.getElementById('editNpcId').value = npc.id;
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcAssetId').value = npc.assetId;
        document.getElementById('editNpcPrompt').value = npc.personality || npc.systemPrompt || '';
        document.getElementById('editNpcRadius').value = npc.responseRadius;
        
        // Show the modal
        const modal = document.getElementById('npcEditModal');
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading NPC data:', error);
        alert('Failed to load NPC data');
    }
}

async function saveNPCEdit(event) {
    event.preventDefault();
    const npcId = document.getElementById('editNpcId').value;
    
    try {
        const response = await fetch(`/api/npcs/${npcId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                displayName: document.getElementById('editNpcDisplayName').value,
                assetId: document.getElementById('editNpcAssetId').value,
                personality: document.getElementById('editNpcPrompt').value,
                responseRadius: parseInt(document.getElementById('editNpcRadius').value)
            })
        });

        if (!response.ok) throw new Error('Failed to update NPC');

        // Refresh the NPC list
        await loadNPCs();

        // Close the modal
        closeNPCEditModal();
    } catch (error) {
        console.error('Error updating NPC:', error);
        alert('Failed to update NPC');
    }
}

function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function createAsset(event) {
    event.preventDefault();
    
    // Check if game is selected
    const gameId = window.gamesDashboard?.currentGameId;
    if (!gameId) {
        alert('Please select a game before creating assets');
        return;
    }

    const formData = new FormData(event.target);
    formData.append('game_id', gameId);
    // ... rest of asset creation code ...
}

async function createNPC(event) {
    event.preventDefault();
    
    // Check if game is selected
    const gameId = window.gamesDashboard?.currentGameId;
    if (!gameId) {
        alert('Please select a game before creating NPCs');
        return;
    }

    const formData = new FormData(event.target);
    formData.append('game_id', gameId);
    // ... rest of NPC creation code ...
} 