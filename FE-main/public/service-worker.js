// Service Worker for Query Pro - Progressive Web App
// Enables offline functionality, caching, and background sync

const CACHE_NAME = 'query-pro-v2.0.0';
const API_CACHE = 'query-pro-api-v1';
const ASSETS_CACHE = 'query-pro-assets-v1';

// Assets to cache on install
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  // Add your CSS and JS files
];

// API endpoints to cache
const API_ENDPOINTS_TO_CACHE = [
  '/api/complaints',
  '/api/auth/profile',
  '/api/features/tags/popular',
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching app shell');
        return cache.addAll(ASSETS_TO_CACHE).catch(() => {
          console.log('Some assets could not be cached');
        });
      })
      .then(() => {
        console.log('Service Worker installed');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Install error:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE && cacheName !== ASSETS_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - network first strategy with fallback
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  // Skip external URLs and chrome extensions
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful API responses
          if (response.status === 200) {
            const cache = caches.open(API_CACHE);
            cache.then((c) => c.put(event.request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          // Return cached API response if network fails
          return caches.match(event.request)
            .then((response) => {
              if (response) {
                console.log('Returning cached API response');
                return response;
              }
              // Return offline page if no cache
              return caches.match('/offline.html').catch(() => {
                return new Response('Offline - No cached data available', {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: new Headers({
                    'Content-Type': 'text/plain'
                  })
                });
              });
            });
        })
    );
    return;
  }

  // Handle static assets
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }

        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            caches.open(ASSETS_CACHE)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Return offline page or placeholder
            if (event.request.destination === 'document') {
              return caches.match('/offline.html').catch(() => {
                return new Response('Offline - Page not available in cache', {
                  status: 503,
                  statusText: 'Service Unavailable'
                });
              });
            }

            // Return placeholder for other resources
            return new Response('');
          });
      })
  );
});

// Background sync for offline submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-complaints') {
    event.waitUntil(syncComplaints());
  }
});

// Function to sync pending complaints
async function syncComplaints() {
  try {
    // Get pending complaints from IndexedDB
    const db = await openDatabase();
    const pendingComplaints = await getPendingComplaints(db);

    for (const complaint of pendingComplaints) {
      try {
        const response = await fetch('/api/complaints', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getToken()}`
          },
          body: JSON.stringify(complaint)
        });

        if (response.ok) {
          await removePendingComplaint(db, complaint.id);
        }
      } catch (error) {
        console.error('Sync error for complaint:', error);
      }
    }

    // Notify clients about sync completion
    const clients = await self.clients.matchAll();
    clients.forEach((client) => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        synced: pendingComplaints.length
      });
    });
  } catch (error) {
    console.error('Sync failed:', error);
    throw error;
  }
}

// Periodic background sync
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'update-complaints') {
    event.waitUntil(updateComplaintsCache());
  }
});

async function updateComplaintsCache() {
  try {
    const response = await fetch('/api/complaints');
    if (response.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put('/api/complaints', response.clone());
    }
  } catch (error) {
    console.error('Cache update failed:', error);
  }
}

// Helper functions
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('QueryProDB', 1);

    request.upgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-complaints')) {
        db.createObjectStore('pending-complaints', { keyPath: 'id', autoIncrement: true });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function getPendingComplaints(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pending-complaints'], 'readonly');
    const store = transaction.objectStore('pending-complaints');
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function removePendingComplaint(db, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pending-complaints'], 'readwrite');
    const store = transaction.objectStore('pending-complaints');
    const request = store.delete(id);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function getToken() {
  return new Promise((resolve) => {
    const tokenRequest = indexedDB.open('QueryProDB');
    tokenRequest.onsuccess = () => {
      const db = tokenRequest.result;
      if (db.objectStoreNames.contains('auth')) {
        const transaction = db.transaction(['auth'], 'readonly');
        const store = transaction.objectStore('auth');
        const request = store.get('token');
        request.onsuccess = () => resolve(request.result?.value);
      }
    };
  });
}

// Push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const options = {
      body: data.body || 'New notification',
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      tag: data.tag || 'notification',
      requireInteraction: data.requireInteraction || false,
      actions: [
        {
          action: 'open',
          title: 'Open'
        },
        {
          action: 'close',
          title: 'Dismiss'
        }
      ]
    };

    if (data.image) {
      options.image = data.image;
    }

    event.waitUntil(
      self.registration.showNotification(data.title || 'Query Pro', options)
    );
  } catch (error) {
    console.error('Push notification error:', error);
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  // Open the app when notification is clicked
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then((clientList) => {
        // Check if app is already open
        for (let client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if not open
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
  );
});

console.log('Service Worker loaded');
