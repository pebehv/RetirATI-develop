// Theme management functions
function applyTheme(themeMode) {
    if (themeMode === 'oscuro') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}

function applyColorTheme(colorTheme) {
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        switch(colorTheme) {
            case 'azul':
                mainContent.style.background = 'linear-gradient(to right, #1DA9EF, #103A7B)';
                break;
            case 'verde':
                mainContent.style.background = 'linear-gradient(to right, #32C479, #125B1F)';
                break;
            case 'rosado':
            default:
                mainContent.style.background = 'linear-gradient(to right, #f4c4f3, #fc67fa)';
                break;
        }
    }
}

// Initialize theme from data attributes
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const themeMode = body.getAttribute('data-theme-mode');
    const colorTheme = body.getAttribute('data-color-theme');
    
    if (themeMode) {
        applyTheme(themeMode);
    }
    
    if (colorTheme) {
        applyColorTheme(colorTheme);
    }
});

// Export functions for use in other scripts
window.ThemeManager = {
    applyTheme,
    applyColorTheme
}; 