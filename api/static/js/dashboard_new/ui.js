import { state } from './state.js';

export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'error' ? 'bg-red-600' :
        type === 'success' ? 'bg-green-600' :
        'bg-blue-600'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 3000);
    }, 3000);
}

export function showModal(content) {
    console.log('UI.JS: showModal called with content:', content);
    
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    console.log('UI.JS: Created backdrop');

    const modal = document.createElement('div');
    modal.className = 'bg-dark-900 rounded-lg shadow-xl max-w-2xl w-full mx-4';
    console.log('UI.JS: Created modal');

    modal.appendChild(content);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    console.log('UI.JS: Added modal to DOM');

    document.body.style.overflow = 'hidden';
}

export function hideModal() {
    const modal = document.querySelector('.fixed.inset-0');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

export function closeAssetEditModal() {
    const modal = document.getElementById('assetEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

export function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

export function initializeTooltips() {
    const tooltipContent = "Please select a game first";
    
    // Add tooltip attributes to disabled nav items
    ['nav-assets', 'nav-npcs', 'nav-players'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.setAttribute('title', tooltipContent);
            // Optional: Add more sophisticated tooltip library initialization here
        }
    });
}

// Call this in your main initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeTooltips();
});

// Make modal functions globally available
window.showModal = showModal;
window.hideModal = hideModal;
window.closeAssetEditModal = closeAssetEditModal;
window.closeNPCEditModal = closeNPCEditModal; 