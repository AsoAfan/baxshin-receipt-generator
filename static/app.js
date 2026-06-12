// Register service worker once at load.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/service-worker.js", { scope: "/" })
      .then((reg) => {
        console.log("Service Worker registered:", reg.scope);
        setInterval(() => reg.update(), 5 * 60 * 1000);
      })
      .catch((error) => console.log("Service Worker registration failed:", error));
  });
}

let deferredPrompt = null;

function ensureInstallBanner() {
  let banner = document.getElementById("install-banner");
  if (banner) {
    return banner;
  }

  banner = document.createElement("aside");
  banner.id = "install-banner";
  banner.className = "install-banner no-print";
  banner.hidden = true;
  banner.innerHTML = `
    <p class="install-banner-text">Install this app for faster access and offline use.</p>
    <div class="install-banner-actions">
      <button id="install-btn" class="button primary" type="button">Install</button>
      <button id="dismiss-install" class="button ghost" type="button">Later</button>
    </div>
  `;
  document.body.appendChild(banner);
  return banner;
}

function showInstallPrompt() {
  const banner = ensureInstallBanner();
  const installBtn = document.getElementById("install-btn");
  const dismissBtn = document.getElementById("dismiss-install");
  if (!installBtn || !dismissBtn) {
    return;
  }

  banner.hidden = false;

  if (!installBtn.dataset.bound) {
    installBtn.dataset.bound = "true";
    installBtn.addEventListener("click", async () => {
      if (!deferredPrompt) {
        return;
      }
      deferredPrompt.prompt();
      const result = await deferredPrompt.userChoice;
      if (result.outcome === "accepted") {
        deferredPrompt = null;
        banner.hidden = true;
      }
    });
  }

  if (!dismissBtn.dataset.bound) {
    dismissBtn.dataset.bound = "true";
    dismissBtn.addEventListener("click", () => {
      banner.hidden = true;
    });
  }
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  showInstallPrompt();
});

window.addEventListener("appinstalled", () => {
  deferredPrompt = null;
  const banner = document.getElementById("install-banner");
  if (banner) {
    banner.hidden = true;
  }
});

// Initialize IndexedDB for offline data storage
function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ReceiptDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('receipts')) {
        const receiptStore = db.createObjectStore('receipts', { keyPath: 'id', autoIncrement: true });
        receiptStore.createIndex('date', 'created_at', { unique: false });
        receiptStore.createIndex('status', 'status', { unique: false });
      }

      if (!db.objectStoreNames.contains('customers')) {
        const customerStore = db.createObjectStore('customers', { keyPath: 'id', autoIncrement: true });
        customerStore.createIndex('name', 'name', { unique: true });
      }

      if (!db.objectStoreNames.contains('items')) {
        const itemStore = db.createObjectStore('items', { keyPath: 'id', autoIncrement: true });
        itemStore.createIndex('description', 'description', { unique: true });
      }
    };
  });
}

// Store data offline
async function saveOfflineData(storeName, data) {
  try {
    const db = await initDB();
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = typeof data === 'object' && data.id ? store.put(data) : store.add(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Failed to save offline data:', error);
  }
}

// Retrieve offline data
async function getOfflineData(storeName, query) {
  try {
    const db = await initDB();
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = query ? store.get(query) : store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Failed to get offline data:', error);
  }
}

// Check if online
window.addEventListener("online", () => {
  console.log("Back online");
  document.body.classList.remove("offline");
  const banner = document.getElementById("offline-banner");
  if (banner) {
    banner.hidden = true;
  }
});

window.addEventListener("offline", () => {
  console.log("Now offline");
  document.body.classList.add("offline");
  const banner = document.getElementById("offline-banner");
  if (banner) {
    banner.hidden = false;
  }
});

// Check initial online status
if (!navigator.onLine) {
  document.body.classList.add("offline");
  const banner = document.getElementById("offline-banner");
  if (banner) {
    banner.hidden = false;
  }
}

let lastScrollY = 0;

function getScrollContainer() {
  return document.querySelector(".receipt-preview-wrap") || window;
}

function getCurrentScrollY() {
  const container = getScrollContainer();
  if (container === window) {
    return window.scrollY;
  }
  return container.scrollTop;
}

function updateMobileDockVisibility() {
  const isMobile = window.matchMedia("(max-width: 768px)").matches;
  if (!isMobile) {
    document.body.classList.remove("mobile-dock-hidden");
    lastScrollY = 0;
    return;
  }

  const currentScrollY = getCurrentScrollY();
  const delta = currentScrollY - lastScrollY;

  // Keep navbar visible at the top and on first load.
  if (currentScrollY <= 10) {
    document.body.classList.remove("mobile-dock-hidden");
    lastScrollY = currentScrollY;
    return;
  }

  // Ignore tiny jitter to avoid flicker.
  if (Math.abs(delta) <= 2) {
    return;
  }

  // Hide when scrolling down, show when scrolling up.
  document.body.classList.toggle("mobile-dock-hidden", delta > 0);
  lastScrollY = currentScrollY;
}

window.addEventListener("scroll", updateMobileDockVisibility, { passive: true });
window.addEventListener("resize", updateMobileDockVisibility);

// Initialize DB on page load
window.addEventListener("load", () => {
  initDB().catch((err) => console.log("DB init failed:", err));
  const container = getScrollContainer();
  if (container !== window) {
    container.addEventListener("scroll", updateMobileDockVisibility, { passive: true });
  }
  lastScrollY = getCurrentScrollY();
  updateMobileDockVisibility();
});
