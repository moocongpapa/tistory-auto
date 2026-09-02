// Service Worker for Tistory AI Auto-Publisher Push & Background Notification
const CACHE_NAME = 'tistory-ai-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

// Handle Notification Click - Focus or open post URL
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const urlToOpen = event.notification.data && event.notification.data.url ? event.notification.data.url : '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            for (let client of windowClients) {
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Listen for push events (Native Web Push)
self.addEventListener('push', (event) => {
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = { title: '티스토리 AI 알림', body: event.data.text() };
        }
    }

    const title = data.title || '🎉 새 글 발행 완료!';
    const options = {
        body: data.body || '새로운 포스팅이 성공적으로 등록되었습니다.',
        icon: data.icon || '/assets/smartwork/smartwork_icon.png',
        badge: '/assets/smartwork/smartwork_icon.png',
        data: {
            url: data.url || '/'
        },
        vibrate: [200, 100, 200],
        tag: 'tistory-post-' + Date.now(),
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});