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
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';

    const modal = document.createElement('div');
    modal.className = 'bg-dark-900 rounded-lg shadow-xl max-w-2xl w-full mx-4';

    const closeButton = document.createElement('button');
    closeButton.className = 'absolute top-4 right-4 text-gray-400 hover:text-white';
    closeButton.innerHTML = '<i class="fas fa-times"></i>';
    closeButton.onclick = hideModal;

    modal.appendChild(closeButton);
    modal.appendChild(content);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

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

// Make modal functions globally available
window.showModal = showModal;
window.hideModal = hideModal;
window.closeAssetEditModal = closeAssetEditModal;
window.closeNPCEditModal = closeNPCEditModal; 