/**
 * Main Application Module
 * Initializes the app and provides utility functions
 */

// Toast notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : '✕'}</span>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Initialize app
async function initApp() {
    console.log('🚀 PolyIITB initializing...');

    // Check auth state
    updateUIForAuthState();

    // Load markets
    await loadMarkets();

    // If logged in, refresh user data
    if (TokenManager.isLoggedIn()) {
        await refreshUserData();
    }

    console.log('PolyIITB ready!');
}

// Seed data for development
async function seedData() {
    try {
        const response = await fetch('/api/seed', { method: 'POST' });
        const result = await response.json();
        console.log('Seed result:', result);

        if (result.message) {
            showToast(result.message, 'success');
            await loadMarkets();
        }
    } catch (error) {
        console.error('Seed failed:', error);
    }
}

// Make seedData available globally for console access
window.seedData = seedData;

// Close modals on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAuthModal();
        closeMarketModal();
    }
});

// Smooth scroll for anchor links
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Skip if href is just '#' or '#portfolio' (handled elsewhere)
            if (href === '#' || href === '#portfolio') {
                return;
            }
            try {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            } catch (err) {
                // Invalid selector, ignore
            }
        });
    });
});

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
