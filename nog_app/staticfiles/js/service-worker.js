// Service Worker for handling push notifications
// Place this at the root: /service-worker.js

self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    self.clients.claim();
});

self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);

    let notificationData = {
        title: 'Nog Off',
        body: 'You have a notification',
        icon: '/static/images/icon.png',
        badge: '/static/images/badge.png',
        tag: 'nogoff-notification',
    };

    if (event.data) {
        try {
            const data = event.data.json();
            if (data.notification) {
                notificationData = {
                    ...notificationData,
                    ...data.notification
                };
            }
        } catch (e) {
            notificationData.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    event.notification.close();

    // Handle notification click - navigate to app
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});
