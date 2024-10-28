// In your asset creation form handler
async function handleAssetSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('storage_type', storageTypeSelect.value);  // New field
    formData.append('data', JSON.stringify({
        assetId: assetIdInput.value,
        name: nameInput.value,
        // ... other asset data ...
    }));

    try {
        const response = await fetch('/api/assets', {
            method: 'POST',
            body: formData
        });
        // ... handle response ...
    } catch (error) {
        console.error('Error:', error);
    }
}

// Add the storage type selector to your form
const storageTypeSelect = document.createElement('select');
storageTypeSelect.innerHTML = `
    <option value="">Select storage type</option>
    <option value="npcs">NPCs</option>
    <option value="vehicles">Vehicles</option>
    <option value="buildings">Buildings</option>
    <option value="props">Props</option>
`;
storageTypeSelect.required = true;

// Add it to your form
const form = document.querySelector('#asset-form');  // Adjust selector as needed
form.insertBefore(storageTypeSelect, form.querySelector('button[type="submit"]'));
