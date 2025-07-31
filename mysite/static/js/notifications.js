// Real-time Notification System for PMS

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    show(message, type = 'info', duration = 5000, options = {}) {
        const notification = {
            id: Date.now() + Math.random(),
            message,
            type,
            duration,
            timestamp: new Date(),
            ...options
        };

        this.notifications.push(notification);
        this.render(notification);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification.id);
            }, duration);
        }

        // Show browser notification if enabled
        if (options.browser && 'Notification' in window && Notification.permission === 'granted') {
            new Notification(options.title || 'PMS Notification', {
                body: message,
                icon: '/static/images/logo.jpg',
                tag: notification.id
            });
        }

        return notification.id;
    }

    render(notification) {
        const element = document.createElement('div');
        element.id = `notification-${notification.id}`;
        element.className = `alert alert-${this.getBootstrapType(notification.type)} alert-dismissible fade show`;
        element.style.cssText = `
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border: none;
            border-radius: 8px;
            animation: slideInRight 0.3s ease-out;
        `;

        const icon = this.getIcon(notification.type);
        const timeAgo = this.getTimeAgo(notification.timestamp);

        element.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="me-2">
                    <i class="${icon}"></i>
                </div>
                <div class="flex-grow-1">
                    ${notification.title ? `<strong>${notification.title}</strong><br>` : ''}
                    ${notification.message}
                    <small class="d-block text-muted mt-1">${timeAgo}</small>
                </div>
                <button type="button" class="btn-close" onclick="notificationManager.remove(${notification.id})"></button>
            </div>
        `;

        this.container.appendChild(element);

        // Add slide-in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        if (!document.querySelector('#notification-styles')) {
            style.id = 'notification-styles';
            document.head.appendChild(style);
        }
    }

    remove(id) {
        const element = document.getElementById(`notification-${id}`);
        if (element) {
            element.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, 300);
        }

        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    clear() {
        this.notifications.forEach(notification => {
            this.remove(notification.id);
        });
    }

    getBootstrapType(type) {
        const typeMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
            'primary': 'primary'
        };
        return typeMap[type] || 'info';
    }

    getIcon(type) {
        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle',
            'primary': 'fas fa-bell'
        };
        return iconMap[type] || 'fas fa-bell';
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return timestamp.toLocaleDateString();
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', 5000, options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', 8000, options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', 6000, options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', 5000, options);
    }
}

// Initialize global notification manager
const notificationManager = new NotificationManager();

// Real-time event monitoring
class EventMonitor {
    constructor() {
        this.lastEventCheck = new Date();
        this.checkInterval = 10000; // Check every 10 seconds
        this.init();
    }

    init() {
        this.startMonitoring();
    }

    startMonitoring() {
        setInterval(() => {
            this.checkForEvents();
        }, this.checkInterval);
    }

    async checkForEvents() {
        try {
            // Check for new parking events
            const response = await fetch('/api/dashboard-analytics/');
            const data = await response.json();
            
            if (data.recent_activity && data.recent_activity.length > 0) {
                const latestActivity = data.recent_activity[0];
                const activityTime = new Date(latestActivity.start_time);
                
                // Only show notification for very recent activities (last 30 seconds)
                if (activityTime > new Date(Date.now() - 30000)) {
                    this.showActivityNotification(latestActivity);
                }
            }
        } catch (error) {
            console.error('Error checking for events:', error);
        }
    }

    showActivityNotification(activity) {
        let message, type, title;
        
        switch (activity.status) {
            case 'active':
                title = 'Vehicle Entry';
                message = `${activity.vehicle_number} entered slot ${activity.slot_id}`;
                type = 'success';
                break;
            case 'completed':
                title = 'Vehicle Exit';
                message = `${activity.vehicle_number} left slot ${activity.slot_id}. Fee: ₹${activity.fee || 0}`;
                type = 'info';
                break;
            case 'pending':
                title = 'Slot Reserved';
                message = `Slot ${activity.slot_id} reserved for ${activity.vehicle_number}`;
                type = 'warning';
                break;
            default:
                return; // Don't show notification for unknown status
        }

        notificationManager.show(message, type, 6000, {
            title,
            browser: true
        });
    }
}

// Initialize event monitor on dashboard pages
if (window.location.pathname.includes('dashboard') || window.location.pathname.includes('admin')) {
    const eventMonitor = new EventMonitor();
}

// Utility functions for manual notifications
window.showNotification = (message, type = 'info', options = {}) => {
    return notificationManager.show(message, type, 5000, options);
};

window.showSuccess = (message, options = {}) => {
    return notificationManager.success(message, options);
};

window.showError = (message, options = {}) => {
    return notificationManager.error(message, options);
};

window.showWarning = (message, options = {}) => {
    return notificationManager.warning(message, options);
};

window.showInfo = (message, options = {}) => {
    return notificationManager.info(message, options);
};
