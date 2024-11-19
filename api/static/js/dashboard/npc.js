// Import dependencies
import { showNotification, hideModal } from './ui.js';
import { debugLog } from './utils.js';

// State
let currentNPCs = [];

// NPC Management Functions
export function editNPC(npcId) {
    debugLog('Editing NPC', { npcId });
    try {
        const npc = currentNPCs.find(n => n.npcId === npcId);
        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }
        debugLog('Found NPC to edit', npc);

        document.getElementById('editNpcId').value = npc.npcId;
        document.getElementById('editNpcDisplayName').value = npc.displayName;
        document.getElementById('editNpcModel').value = npc.model || '';
        document.getElementById('editNpcRadius').value = npc.responseRadius || 20;
        document.getElementById('editNpcPrompt').value = npc.systemPrompt || '';

        const abilitiesContainer = document.getElementById('editAbilitiesCheckboxes');
        populateAbilityCheckboxes(abilitiesContainer, npc.abilities || []);

        document.getElementById('npcEditModal').style.display = 'block';
    } catch (error) {
        console.error('Error opening NPC edit modal:', error);
        showNotification('Failed to open edit modal', 'error');
    }
}

export async function saveNPCEdit(event) {
    event.preventDefault();
    const npcId = document.getElementById('editNpcId').value;

    try {
        debugLog('Saving NPC edit', { npcId });

        const selectedAbilities = Array.from(
            document.querySelectorAll('#editAbilitiesCheckboxes input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        const npc = currentNPCs.find(n => n.npcId === npcId);
        if (!npc) {
            throw new Error(`NPC not found: ${npcId}`);
        }

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            model: document.getElementById('editNpcModel').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            systemPrompt: document.getElementById('editNpcPrompt').value,
            abilities: selectedAbilities,
            assetId: npc.assetId
        };

        debugLog('Update data:', data);

        const response = await fetch(`/api/npcs/${npc.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to update NPC');

        showNotification('NPC updated successfully', 'success');
        hideModal();
        loadNPCs();
    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes', 'error');
    }
}

// Export other NPC-related functions... 