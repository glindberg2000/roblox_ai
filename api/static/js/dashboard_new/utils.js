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