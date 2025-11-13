// Client-side JavaScript for OsMEN Dashboard

function getCsrfToken() {
    return window.OSMEN_CSRF_TOKEN || '';
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('OsMEN Dashboard loaded');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    setInterval(function() {
        if (window.htmx) {
            htmx.ajax('GET', '/api/status', {
                target: '#status-container',
                swap: 'innerHTML'
            });
        }
    }, 30000);
});

if (window.htmx) {
    document.body.addEventListener('htmx:configRequest', function (event) {
        event.detail.headers['X-CSRF-Token'] = getCsrfToken();
    });
}

document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.status >= 400) {
        console.error('Request failed:', event.detail.xhr.status);
    }
});
