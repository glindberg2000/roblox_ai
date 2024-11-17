window.handleGameSubmit = async function(event) {
    event.preventDefault();
    
    const submitButton = event.target.querySelector('button[type="submit"]');
    if (submitButton.disabled) return false;
    submitButton.disabled = true;

    try {
        const formData = new FormData(event.target);
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            cloneFrom: formData.get('cloneFrom') || null
        };
        
        console.log('Creating game:', data);
        
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create game');
        }

        const result = await response.json();
        console.log('Game created:', result);
        
        event.target.reset();
        loadGames();
        showNotification('Game created successfully', 'success');
        
    } catch (error) {
        console.error('Error creating game:', error);
        showNotification(error.message, 'error');
    } finally {
        submitButton.disabled = false;
    }
    
    return false;
};







