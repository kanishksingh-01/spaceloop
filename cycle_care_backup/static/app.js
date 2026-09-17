/**
 * Cycle Care & Partner Connect - Shared Client Utilities
 */

function getUser() {
  try {
    const raw = localStorage.getItem("cycle_user");
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function setUser(user) {
  localStorage.setItem("cycle_user", JSON.stringify(user));
}

function requireUser(expectedRole = null) {
  const user = getUser();
  if (!user) {
    window.location.href = "/login";
    return null;
  }
  if (expectedRole && user.role !== expectedRole) {
    if (user.role === "partner") {
      window.location.href = "/partner";
    } else {
      window.location.href = "/dashboard";
    }
    return null;
  }
  return user;
}

function logout() {
  localStorage.removeItem("cycle_user");
  window.location.href = "/login";
}

async function apiGet(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: "Request failed" }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error("API GET Error:", e);
    throw e;
  }
}

async function apiPost(url, data) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: "Request failed" }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error("API POST Error:", e);
    throw e;
  }
}

// ---------- THEME MANAGEMENT (DARK / LIGHT MODE) ----------
function initTheme() {
  const savedTheme = localStorage.getItem("cycle_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcons(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("cycle_theme", next);
  updateThemeIcons(next);
  showToast(`Switched to ${next === "dark" ? "Dark" : "Light"} Mode`);
}

function updateThemeIcons(theme) {
  document.querySelectorAll(".theme-icon").forEach(el => {
    el.innerText = theme === "dark" ? "☀️" : "🌙";
  });
}

// ---------- COMPANION NAME CUSTOMIZATION ----------
function getCompanionName() {
  return localStorage.getItem("companion_name") || "Aura";
}

function setCompanionName(name) {
  const clean = name ? name.trim() : "Aura";
  localStorage.setItem("companion_name", clean || "Aura");
  showToast(`Companion name set to ${clean}!`);
  return clean;
}

// ---------- DISCREET PANIC SHIELD ----------
function togglePanicShield() {
  if (document.body.classList.contains("panic-shield-active")) {
    exitPanicShield();
  } else {
    document.body.classList.add("panic-shield-active");
  }
}

function exitPanicShield() {
  document.body.classList.remove("panic-shield-active");
  localStorage.removeItem("panic_shield");
}

function initPanicShield() {
  // Clear any sticky panic shield from previous sessions so user is never trapped
  localStorage.removeItem("panic_shield");
  document.body.classList.remove("panic-shield-active");

  if (!document.getElementById("panicShieldDocument")) {
    const decoy = document.createElement("div");
    decoy.id = "panicShieldDocument";
    decoy.innerHTML = `
      <button class="exit-panic-btn" onclick="exitPanicShield()" title="Resume private app view">
        ✕ Exit Discreet View (Esc)
      </button>
      <h1>BIOCHEM 301: Advanced Cellular Metabolism & Enzymatic Pathways</h1>
      <p style="color:#666; font-size:12px;">Last modified: Today, 11:42 AM • Shared with Course Study Group</p>
      
      <h2>1. Glycolysis & Substrate-Level Phosphorylation</h2>
      <p>The hexokinase-catalyzed step is thermodynamically irreversible under standard physiological conditions (ΔG°' = -16.7 kJ/mol). Notice how the glucose-6-phosphate intermediate is trapped intracellularly due to its negative charge.</p>
      
      <h2>2. Citric Acid Cycle Regulation</h2>
      <p>Isocitrate dehydrogenase functions as the rate-limiting step, exhibiting positive cooperativity with ADP and allosteric inhibition by elevated ATP and NADH ratios. Review Figure 4.2 for the succinate dehydrogenase complex mechanism.</p>
      
      <h2>3. Homework & Lab Deadlines</h2>
      <p>• Thursday: Submit Spectrophotometry calibration curve writeup.<br>• Next Tuesday: Midterm examination covering modules 1 through 5.</p>
    `;
    const shell = document.querySelector(".app-shell") || document.body;
    shell.appendChild(decoy);
  }

  // Keybind: Pressing Escape exits or toggles Panic Shield
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      togglePanicShield();
    }
  });
}

// Toast notification helper
function showToast(message, type = "info") {
  let toast = document.getElementById("appToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "appToast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: #341D2C;
      color: #FFF;
      padding: 12px 24px;
      border-radius: 9999px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.18);
      z-index: 9999;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
      opacity: 0;
      pointer-events: none;
    `;
    document.body.appendChild(toast);
  }
  toast.innerText = message;
  toast.style.opacity = "1";
  toast.style.transform = "translateX(-50%) translateY(0)";

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(-50%) translateY(10px)";
  }, 3500);
}

// ---------- PWA INSTALL & SERVICE WORKER ----------
let deferredInstallPrompt = null;

function initPWA() {
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js')
        .then((reg) => console.log('Service Worker registered with scope:', reg.scope))
        .catch((err) => console.warn('Service Worker registration failed:', err));
    });
  }

  // Handle Chrome / Android / Desktop Install Prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    const installBtns = document.querySelectorAll('.btn-install-pwa');
    installBtns.forEach(b => b.style.display = 'inline-flex');
  });

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    const installBtns = document.querySelectorAll('.btn-install-pwa');
    installBtns.forEach(b => b.style.display = 'none');
    showToast('Cycle Care installed successfully! Enjoy your native app experience. 🎉');
  });
}

function promptInstallApp() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the PWA install prompt');
      }
      deferredInstallPrompt = null;
    });
  } else {
    // Check if iOS
    const isIos = /iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase());
    if (isIos) {
      alert("To install Cycle Care on iPhone/iPad:\n1. Tap the Share button (square with arrow up ⎋) at the bottom of Safari.\n2. Scroll down and tap 'Add to Home Screen' ➕.\n3. Tap 'Add' to run it as a standalone app!");
    } else {
      alert("To install on Desktop or Mobile: Look for the 'Install' icon ⊕ in your browser address bar, or use Chrome/Edge Menu > 'Install Cycle Care'.");
    }
  }
}

// Initialize theme immediately to prevent flashing
initTheme();

document.addEventListener("DOMContentLoaded", () => {
  initPanicShield();
  initPWA();
  initTheme();
});
