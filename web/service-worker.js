self.addEventListener('install', function(event) {
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
        const title = event.data.title || "天堂W BOSS 預警";
        const options = {
            body: event.data.body || "",
            icon: './icons/icon-192.png',
            badge: './icons/icon-192.png',
            vibrate: [300, 100, 300, 100, 400],
            data: {
                url: self.location.origin + self.location.pathname.replace('service-worker.js', 'index.html')
            }
        };
        self.registration.showNotification(title, options);
    }
});

self.addEventListener('push', function(event) {
    if (event.data) {
        let title = "天堂W BOSS 預警";
        let body = "";
        
        try {
            const data = event.data.json();
            title = data.title || title;
            body = data.body || body;
        } catch (e) {
            body = event.data.text();
        }

        const options = {
            body: body,
            icon: './icons/icon-192.png',
            badge: './icons/icon-192.png',
            vibrate: [300, 100, 300, 100, 400],
            data: {
                url: self.location.origin + self.location.pathname.replace('service-worker.js', 'index.html')
            }
        };

        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    let targetUrl = './index.html';
    if (event.notification.data && event.notification.data.url) {
        targetUrl = event.notification.data.url;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url.startsWith(self.location.origin) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
