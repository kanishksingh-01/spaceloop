/**
 * SpaceLoop Client-Side Interactive Engine
 * Handles Persona Switching, GPS Radar, QR Verification, LoopBot Chat, and Pricing Calculators.
 */

// Global Toast System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColors = {
        success: 'bg-emerald-600 text-white',
        error: 'bg-rose-600 text-white',
        info: 'bg-indigo-600 text-white',
        warning: 'bg-amber-600 text-white'
    };
    const icon = {
        success: 'fa-circle-check',
        error: 'fa-circle-exclamation',
        info: 'fa-circle-info',
        warning: 'fa-triangle-exclamation'
    }[type] || 'fa-bell';

    toast.className = `pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-sm font-medium transition-all duration-300 transform translate-y-2 opacity-0 ${bgColors[type] || bgColors.info}`;
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', '-translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Persona Switcher
async function switchPersona(role) {
    try {
        const res = await fetch('/api/persona/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona: role })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Switched view to ${data.persona === 'owner' ? 'Host / Space Owner' : 'Student / Seeker'}`, 'success');
            setTimeout(() => {
                window.location.href = data.redirect || '/';
            }, 500);
        }
    } catch (err) {
        showToast('Failed to switch persona', 'error');
    }
}

// LoopBot AI Concierge
let loopbotOpen = false;
function toggleLoopBot() {
    const chatWin = document.getElementById('loopbot-window');
    if (!chatWin) return;
    loopbotOpen = !loopbotOpen;
    if (loopbotOpen) {
        chatWin.classList.remove('hidden');
        document.getElementById('loopbot-input')?.focus();
    } else {
        chatWin.classList.add('hidden');
    }
}

async function sendLoopBotMessage() {
    const input = document.getElementById('loopbot-input');
    const messages = document.getElementById('loopbot-messages');
    if (!input || !messages) return;

    const userText = input.value.trim();
    if (!userText) return;

    // Append User message
    const userBubble = document.createElement('div');
    userBubble.className = 'flex justify-end';
    userBubble.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 text-xs max-w-[85%] shadow-sm">
            ${userText}
        </div>
    `;
    messages.appendChild(userBubble);
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    // Loading indicator
    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'flex justify-start items-center gap-2';
    loadingBubble.id = 'loopbot-loading';
    loadingBubble.innerHTML = `
        <div class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="bg-gray-100 text-gray-500 rounded-2xl rounded-tl-none px-3 py-2 text-xs">
            <i class="fa-solid fa-circle-notch fa-spin"></i> LoopBot thinking...
        </div>
    `;
    messages.appendChild(loadingBubble);
    messages.scrollTop = messages.scrollHeight;

    try {
        const spaceIdElem = document.getElementById('current-space-id');
        const spaceId = spaceIdElem ? spaceIdElem.value : null;

        const res = await fetch('/api/concierge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userText, space_id: spaceId })
        });
        const data = await res.json();
        loadingBubble.remove();

        const botBubble = document.createElement('div');
        botBubble.className = 'flex justify-start items-start gap-2';
        botBubble.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs mt-1 shrink-0">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bg-gray-100 text-gray-800 rounded-2xl rounded-tl-none px-4 py-2.5 text-xs max-w-[85%] shadow-sm whitespace-pre-line leading-relaxed">
                ${data.reply || 'I am having trouble answering right now, please try again.'}
            </div>
        `;
        messages.appendChild(botBubble);
        messages.scrollTop = messages.scrollHeight;
    } catch (err) {
        loadingBubble.remove();
        showToast('Concierge connection issue', 'warning');
    }
}
