export function debugLog(title, data) {
    // You can set this to false in production
    const DEBUG = true;
    
    if (DEBUG) {
        console.log(`=== ${title} ===`);
        console.log(JSON.stringify(data, null, 2));
        console.log('=================');
    }
}

export function validateData(data, schema) {
    // Basic data validation helper
    for (const [key, requirement] of Object.entries(schema)) {
        if (requirement.required && !data[key]) {
            throw new Error(`Missing required field: ${key}`);
        }
    }
    return true;
}

// Make debug functions globally available if needed
window.debugLog = debugLog;

export function validateAsset(data) {
    const required = ['name', 'assetId', 'type'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}

export function validateNPC(data) {
    const required = ['displayName', 'assetId', 'systemPrompt'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}

export function validateNPCData(data) {
    // Required fields
    const required = {
        displayName: 'Display Name',
        assetId: 'Model',
        systemPrompt: 'System Prompt',
        responseRadius: 'Response Radius'
    };

    // Check required fields
    for (const [field, label] of Object.entries(required)) {
        if (!data[field] || data[field] === '') {
            throw new Error(`${label} is required`);
        }
    }

    // Validate response radius
    const radius = parseInt(data.responseRadius);
    if (isNaN(radius) || radius < 1 || radius > 100) {
        throw new Error('Response Radius must be between 1 and 100');
    }

    // Validate abilities array
    if (!Array.isArray(data.abilities)) {
        throw new Error('Invalid abilities format');
    }

    return true;
}

// Make validation function globally available
window.validateNPCData = validateNPCData;