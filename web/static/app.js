// Client-side JavaScript for OsMEN Dashboard

document.addEventListener('DOMContentLoaded', function() {
    console.log('OsMEN Dashboard loaded');
    
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Add any additional client-side interactivity here
    
    // Auto-refresh status every 30 seconds
    setInterval(function() {
        htmx.ajax('GET', '/api/status', {
            target: '#status-container',
            swap: 'innerHTML'
        });
    }, 30000);
});

document.body.addEventListener('htmx:configRequest', function(event) {
    if (window.OSMEN_CSRF_TOKEN) {
        event.detail.headers['X-CSRF-Token'] = window.OSMEN_CSRF_TOKEN;
    }
});

// Handle HTMX events
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.status >= 400) {
        console.error('Request failed:', event.detail.xhr.status);
    }
});
