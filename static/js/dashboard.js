function populateAbilityCheckboxes(container, selectedAbilities = []) {
    container.innerHTML = '';
    Object.entries(ABILITY_CONFIG).forEach(([key, ability]) => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-2';
        div.innerHTML = `
            <input type="checkbox" 
                   id="ability_${key}" 
                   name="abilities" 
                   value="${key}"
                   ${selectedAbilities.includes(key) ? 'checked' : ''}
                   class="form-checkbox h-4 w-4 text-blue-600">
            <label for="ability_${key}" class="flex items-center space-x-2">
                <i class="${ability.icon}"></i>
                <span>${ability.label}</span>
            </label>
        `;
        container.appendChild(div);
    });
}

// Call this when loading the form
document.addEventListener('DOMContentLoaded', () => {
    const abilityContainer = document.getElementById('abilitiesCheckboxes');
    if (abilityContainer) {
        populateAbilityCheckboxes(abilityContainer);
    }
});

// Modify your existing NPC card rendering to include ability icons
function renderNPCCard(npc) {
    // ... existing card HTML ...
    const abilitiesHTML = npc.abilities.map(ability => {
        const abilityConfig = ABILITY_CONFIG[ability];
        return `<i class="${abilityConfig?.icon || 'fas fa-question'}" 
                   title="${abilityConfig?.label || ability}"
                   class="text-gray-300 mr-2"></i>`;
    }).join('');
    
    // Add this to your card HTML where you want to display the abilities
    `<div class="mt-2 flex flex-wrap gap-2">
        ${abilitiesHTML}
    </div>`
    // ... rest of the card HTML ...
}
