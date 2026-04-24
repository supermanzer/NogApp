// Push notification handler for the NogApp
// Include this in your base template via: <script src="{% static 'js/push-notifications.js' %}"></script>

class PushNotificationManager {
    constructor() {
        this.registration = null;
        this.subscription = null;
        this.publicKey = null;
    }

    /**
     * Initialize push notifications
     * Call this on page load
     */
    async init() {
        console.log('Initializing push notifications...');

        // Check if browser supports Service Workers and Push API
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push notifications not supported in this browser');
            return false;
        }

        try {
            // Register service worker
            this.registration = await navigator.serviceWorker.register(
                '/static/js/service-worker.js'
            );
            console.log('Service Worker registered successfully');

            // Get VAPID public key from server
            const keyResponse = await fetch('/api/push/public-key/');
            if (!keyResponse.ok) {
                console.warn('Unable to fetch push public key');
                return false;
            }

            const keyData = await keyResponse.json();
            this.publicKey = keyData.publicKey;

            // Check if already subscribed
            this.subscription = await this.registration.pushManager.getSubscription();

            if (this.subscription) {
                console.log('Already subscribed to push notifications');
                return true;
            } else {
                console.log('Not yet subscribed to push notifications');
                return true;
            }
        } catch (error) {
            console.error('Error initializing push notifications:', error);
            return false;
        }
    }

    /**
     * Subscribe to push notifications
     */
    async subscribe() {
        if (!this.registration || !this.publicKey) {
            console.error('Push notifications not initialized. Call init() first.');
            return false;
        }

        try {
            // Check if already subscribed
            let subscription = await this.registration.pushManager.getSubscription();

            if (subscription) {
                console.log('Already subscribed to push notifications');
                return true;
            }

            // Subscribe to push notifications
            subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicKey)
            });

            console.log('Push subscription successful:', subscription);

            // Send subscription to server
            const response = await fetch('/api/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();
            console.log('Server response:', data);

            this.subscription = subscription;
            return true;

        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            return false;
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.registration) {
            console.error('Push notifications not initialized. Call init() first.');
            return false;
        }

        try {
            const subscription = await this.registration.pushManager.getSubscription();

            if (!subscription) {
                console.log('Not subscribed to push notifications');
                return true;
            }

            // Send unsubscription to server
            const response = await fetch('/api/push/unsubscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            // Unsubscribe from push manager
            const success = await subscription.unsubscribe();
            console.log('Unsubscribed from push notifications:', success);

            this.subscription = null;
            return success;

        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
            return false;
        }
    }

    /**
     * Check if currently subscribed
     */
    async isSubscribed() {
        if (!this.registration) {
            return false;
        }

        try {
            const subscription = await this.registration.pushManager.getSubscription();
            return subscription !== null;
        } catch (error) {
            console.error('Error checking subscription status:', error);
            return false;
        }
    }

    /**
     * Get current subscription
     */
    async getSubscription() {
        if (!this.registration) {
            return null;
        }

        try {
            return await this.registration.pushManager.getSubscription();
        } catch (error) {
            console.error('Error getting subscription:', error);
            return null;
        }
    }

    /**
     * Request notification permission
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('Notifications not supported');
            return false;
        }

        if (Notification.permission === 'granted') {
            console.log('Notification permission already granted');
            return true;
        }

        if (Notification.permission === 'denied') {
            console.warn('Notification permission denied');
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }

    /**
     * Helper: Convert VAPID public key from base64 to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    /**
     * Helper: Get CSRF token from cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;

        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        return cookieValue;
    }
}

// Create global instance
const pushNotifications = new PushNotificationManager();

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await pushNotifications.init();
});
