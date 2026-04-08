// Settings Page JavaScript

// Load user data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    loadUserPreferences();
    loadScreenshotInterval();
    initializeThemeButtons();
});

// Load user profile information
function loadUserProfile() {
    const userName = sessionStorage.getItem('userName');
    const userEmail = sessionStorage.getItem('userEmail');
    const userRole = sessionStorage.getItem('userRole') || 'User';

    document.getElementById('userName').textContent = userName || 'User Name';
    document.getElementById('userEmail').textContent = userEmail || 'user@example.com';
    document.getElementById('userRole').textContent = userRole;
}

// Load user preferences from localStorage
function loadUserPreferences() {
    // Load language
    const savedLanguage = localStorage.getItem('appLanguage') || 'en';
    document.getElementById('languageSelect').value = savedLanguage;

    // Load remember me
    const rememberMe = localStorage.getItem('rememberMe') === 'true';
    document.getElementById('rememberMe').checked = rememberMe;

    // Load theme
    const savedTheme = localStorage.getItem('appTheme') || 'light';
    setActiveTheme(savedTheme);

    // Load notification preferences
    const desktopNotif = localStorage.getItem('desktopNotifications') !== 'false';
    const soundAlerts = localStorage.getItem('soundAlerts') === 'true';
    const idleWarnings = localStorage.getItem('idleWarnings') !== 'false';

    document.getElementById('desktopNotif').checked = desktopNotif;
    document.getElementById('soundAlerts').checked = soundAlerts;
    document.getElementById('idleWarnings').checked = idleWarnings;

    // Load session timeout
    const sessionTimeout = localStorage.getItem('sessionTimeout') || 'never';
    document.getElementById('sessionTimeout').value = sessionTimeout;
}

// Fetch screenshot interval from backend
async function loadScreenshotInterval() {
    try {
        // Get user info from sessionStorage
        const userEmail = sessionStorage.getItem('userEmail');
        const staffId = sessionStorage.getItem('staffId');
        
        if (!userEmail && !staffId) {
            document.getElementById('screenshotInterval').textContent = '1 minute';
            return;
        }
        
        let payload = {};
        if (staffId) {
            payload.staff_id = staffId;
        } else if (userEmail) {
            payload.email = userEmail;
        }
        
        const response = await fetch('/get_screenshot_time_interval', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data && typeof data.screenshot_interval !== 'undefined') {
            const minutes = data.screenshot_interval;
            const minuteLabel = minutes === 1 ? 'minute' : 'minutes';
            document.getElementById('screenshotInterval').textContent = `${minutes} ${minuteLabel}`;
        } else {
            document.getElementById('screenshotInterval').textContent = '1 minute';
        }
    } catch (error) {
        console.error('Failed to load screenshot interval:', error);
        document.getElementById('screenshotInterval').textContent = '1 minute';
    }
}

// Initialize theme buttons
function initializeThemeButtons() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    
    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const theme = this.getAttribute('data-theme');
            setActiveTheme(theme);
            localStorage.setItem('appTheme', theme);
            applyTheme(theme);
            
            Toastify({
                text: `Theme changed to ${theme}`,
                duration: 2000,
                gravity: "top",
                position: "right",
                backgroundColor: "#006039",
            }).showToast();
        });
    });
}

// Set active theme button
function setActiveTheme(theme) {
    const themeButtons = document.querySelectorAll('.theme-btn');
    themeButtons.forEach(button => {
        if (button.getAttribute('data-theme') === theme) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

// Apply theme to the page
function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    } else if (theme === 'light') {
        document.body.classList.remove('dark-mode');
    } else if (theme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
}

// Language change handler
document.getElementById('languageSelect').addEventListener('change', function() {
    const language = this.value;
    localStorage.setItem('appLanguage', language);
    
    Toastify({
        text: `Language changed to ${language === 'en' ? 'English' : 'Turkish'}`,
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Remember me toggle handler
document.getElementById('rememberMe').addEventListener('change', function() {
    localStorage.setItem('rememberMe', this.checked);
    
    Toastify({
        text: this.checked ? 'Remember me enabled' : 'Remember me disabled',
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Desktop notifications toggle handler
document.getElementById('desktopNotif').addEventListener('change', function() {
    localStorage.setItem('desktopNotifications', this.checked);
    
    if (this.checked && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    Toastify({
        text: this.checked ? 'Desktop notifications enabled' : 'Desktop notifications disabled',
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Sound alerts toggle handler
document.getElementById('soundAlerts').addEventListener('change', function() {
    localStorage.setItem('soundAlerts', this.checked);
    
    Toastify({
        text: this.checked ? 'Sound alerts enabled' : 'Sound alerts disabled',
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Idle warnings toggle handler
document.getElementById('idleWarnings').addEventListener('change', function() {
    localStorage.setItem('idleWarnings', this.checked);
    
    Toastify({
        text: this.checked ? 'Idle warnings enabled' : 'Idle warnings disabled',
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Session timeout handler
document.getElementById('sessionTimeout').addEventListener('change', function() {
    const timeout = this.value;
    localStorage.setItem('sessionTimeout', timeout);
    
    Toastify({
        text: `Session timeout set to ${timeout === 'never' ? 'Never' : timeout}`,
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
});

// Clear cache function
function clearCache() {
    if (confirm('Are you sure you want to clear the cache? This will remove temporary data.')) {
        const userEmail = sessionStorage.getItem('userEmail');
        
        fetch('/clear_cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: userEmail })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Toastify({
                    text: 'Cache cleared successfully',
                    duration: 2000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#006039",
                }).showToast();
            } else {
                throw new Error(data.message || 'Failed to clear cache');
            }
        })
        .catch(error => {
            Toastify({
                text: error.message || 'Failed to clear cache',
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "#e74c3c",
            }).showToast();
        });
    }
}

// Export data function
function exportData() {
    const userEmail = sessionStorage.getItem('userEmail');
    
    Toastify({
        text: 'Preparing data export...',
        duration: 2000,
        gravity: "top",
        position: "right",
        backgroundColor: "#006039",
    }).showToast();
    
    fetch('/export_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: userEmail })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `user_data_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        Toastify({
            text: 'Data exported successfully',
            duration: 2000,
            gravity: "top",
            position: "right",
            backgroundColor: "#006039",
        }).showToast();
    })
    .catch(error => {
        Toastify({
            text: 'Failed to export data',
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#e74c3c",
        }).showToast();
    });
}

// Reset settings function
function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to default? This action cannot be undone.')) {
        // Clear all localStorage settings
        localStorage.removeItem('appLanguage');
        localStorage.removeItem('appTheme');
        localStorage.removeItem('rememberMe');
        localStorage.removeItem('desktopNotifications');
        localStorage.removeItem('soundAlerts');
        localStorage.removeItem('idleWarnings');
        localStorage.removeItem('sessionTimeout');
        
        Toastify({
            text: 'Settings reset successfully. Reloading...',
            duration: 2000,
            gravity: "top",
            position: "right",
            backgroundColor: "#006039",
        }).showToast();
        
        // Reload page after a short delay
        setTimeout(() => {
            location.reload();
        }, 2000);
    }
}

// Logout function
function logoutUser() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear session storage
        sessionStorage.clear();
        
        // Clear remember me if disabled
        if (localStorage.getItem('rememberMe') !== 'true') {
            localStorage.clear();
        }
        
        Toastify({
            text: 'Logging out...',
            duration: 1500,
            gravity: "top",
            position: "right",
            backgroundColor: "#006039",
        }).showToast();
        
        // Redirect to logout endpoint
        setTimeout(() => {
            window.location.href = '/logout';
        }, 1500);
    }
}

// Close settings page
function closeSettings() {
    window.close();
}
