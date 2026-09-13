// SpaceLoop Core Client Application Script

document.addEventListener("DOMContentLoaded", () => {
  initConcierge();
  initAiSearch();
});

/* ==========================================
   AI Concierge (LoopBot)
   ========================================== */
function initConcierge() {
  const openBtn = document.getElementById("openConciergeBtn");
  const closeBtn = document.getElementById("closeConciergeBtn");
  const modal = document.getElementById("conciergeModal");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");

  if (!modal) return;

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      modal.classList.remove("hidden");
      if (input) input.focus();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.classList.add("hidden");
    });
  }

  if (form && input && chatMessages) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      appendChatMessage("user", text);
      input.value = "";

      const typingId = appendTypingIndicator();

      try {
        const resp = await fetch("/api/ai/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [{ role: "user", content: text }],
          }),
        });
        const data = await resp.json();
        removeTypingIndicator(typingId);
        appendChatMessage("assistant", data.reply || "I am here to help you navigate SpaceLoop!");
      } catch (err) {
        removeTypingIndicator(typingId);
        appendChatMessage("assistant", "I had trouble connecting to the AI service. Please try again.");
      }
    });
  }
}

function appendChatMessage(role, text) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "flex gap-2.5 " + (role === "user" ? "justify-end" : "");

  if (role === "assistant") {
    row.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0 text-xs">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="bg-slate-800 text-slate-200 p-3 rounded-2xl rounded-tl-sm max-w-[85%] border border-slate-700/50 leading-relaxed text-xs">
        ${formatMarkdown(text)}
      </div>
    `;
  } else {
    row.innerHTML = `
      <div class="bg-indigo-600 text-white p-3 rounded-2xl rounded-tr-sm max-w-[85%] leading-relaxed text-xs">
        ${escapeHtml(text)}
      </div>
    `;
  }

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = document.getElementById("chatMessages");
  if (!container) return null;

  const id = "typing-" + Date.now();
  const row = document.createElement("div");
  row.id = id;
  row.className = "flex gap-2.5";
  row.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0 text-xs">
      <i class="fa-solid fa-robot"></i>
    </div>
    <div class="bg-slate-800 text-slate-400 px-3 py-2 rounded-2xl rounded-tl-sm text-xs flex items-center gap-1">
      <span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span>
      <span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
      <span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
    </div>
  `;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

function sendQuickPrompt(promptText) {
  const input = document.getElementById("chatInput");
  const form = document.getElementById("chatForm");
  if (input && form) {
    input.value = promptText;
    form.dispatchEvent(new Event("submit"));
  }
}

/* ==========================================
   AI Natural Language Search
   ========================================== */
function initAiSearch() {
  const searchForm = document.getElementById("aiSearchForm");
  const queryInput = document.getElementById("aiQueryInput");

  if (!searchForm || !queryInput) return;

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    executeAiSearch(query);
  });
}

function applySearchPrompt(promptText) {
  const input = document.getElementById("aiQueryInput");
  if (input) {
    input.value = promptText;
    executeAiSearch(promptText);
  }
}

async function executeAiSearch(queryText) {
  const btn = document.getElementById("aiSearchBtn");
  const grid = document.getElementById("spacesGrid");
  const matchHeader = document.getElementById("aiMatchHeader");
  const queryLabel = document.getElementById("aiMatchQueryLabel");
  const noResults = document.getElementById("noResultsState");

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> <span>Matching...</span>`;
  }

  try {
    const resp = await fetch("/api/spaces/ai-match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText }),
    });
    const data = await resp.json();
    const results = data.results || [];

    if (matchHeader && queryLabel) {
      matchHeader.classList.remove("hidden");
      queryLabel.textContent = `Scored & sorted for: "${queryText}"`;
    }

    if (results.length === 0) {
      if (grid) grid.innerHTML = "";
      if (noResults) noResults.classList.remove("hidden");
      return;
    }

    if (noResults) noResults.classList.add("hidden");

    // Render ranked cards
    if (grid) {
      grid.innerHTML = results
        .map((item) => renderSpaceCard(item.space, item))
        .join("");
    }

    // Scroll smoothly to results
    if (matchHeader) {
      matchHeader.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (err) {
    console.error("AI Search failed:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Match with AI</span> <i class="fa-solid fa-arrow-right text-xs group-hover:translate-x-0.5 transition"></i>`;
    }
  }
}

function resetSearch() {
  window.location.href = "/";
}

function sanitizePhotoUrl(url) {
  if (!url || typeof url !== 'string') {
    return 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80';
  }
  const clean = url.trim();
  const lower = clean.toLowerCase();
  if (lower.startsWith('javascript:') || lower.startsWith('vbscript:') || lower.includes('<script')) {
    return 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80';
  }
  if (lower.startsWith('http://') || lower.startsWith('https://') || lower.startsWith('data:image/')) {
    return escapeHtml(clean);
  }
  return 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80';
}

function renderSpaceCard(space, matchMeta) {
  const score = matchMeta?.match_score || space.ai_suitability_score || 92;
  const badge = matchMeta?.match_badge || "Top Match";
  const reasons = matchMeta?.match_reasons || [];
  const reasonHtml =
    reasons.length > 0
      ? `<div class="mb-3 p-2 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
           <i class="fa-solid fa-check text-emerald-400 mr-1"></i> ${escapeHtml(reasons[0])}
         </div>`
      : "";

  const photoUrl = sanitizePhotoUrl(space.photos && space.photos[0]);

  return `
    <div class="space-card group bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden hover:border-indigo-500/50 transition-all duration-300 flex flex-col hover:shadow-xl hover:shadow-indigo-950/40">
      
      <div class="relative aspect-[16/10] overflow-hidden bg-slate-950">
        <img 
          src="${photoUrl}" 
          alt="${escapeHtml(space.title)}" 
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        >
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-black/30"></div>

        <div class="absolute top-3 left-3">
          <span class="px-2.5 py-1 rounded-lg text-xs font-semibold backdrop-blur-md bg-slate-900/80 text-white border border-white/10 shadow-sm">
            ${escapeHtml(space.category)}
          </span>
        </div>

        <div class="absolute top-3 right-3">
          <span class="px-2.5 py-1 rounded-lg text-xs font-bold backdrop-blur-md bg-emerald-500/90 text-white shadow-sm flex items-center gap-1">
            <i class="fa-solid fa-sparkles text-[10px]"></i>
            <span>${score}% ${escapeHtml(badge)}</span>
          </span>
        </div>

        <div class="absolute bottom-3 left-3 right-3 flex items-end justify-between">
          <div>
            <span class="text-2xl font-extrabold text-white">₹${Math.round(space.price_hourly)}</span>
            <span class="text-xs text-slate-300 font-medium">/hour</span>
            <span class="text-xs text-slate-400 ml-1.5">• ₹${Math.round(space.price_daily)}/day</span>
          </div>
          <div class="text-xs text-slate-300 flex items-center gap-1 font-medium bg-black/40 px-2 py-0.5 rounded backdrop-blur-sm">
            <i class="fa-solid fa-star text-amber-400 text-[11px]"></i> ${space.rating || 4.9}
          </div>
        </div>
      </div>

      <div class="p-5 flex flex-col flex-grow">
        <div class="flex items-center gap-2 text-xs text-slate-400 mb-1.5">
          <i class="fa-solid fa-location-dot text-indigo-400"></i>
          <span>${escapeHtml(space.neighborhood || space.city)}, ${escapeHtml(space.state)}</span>
          <span>•</span>
          <span>${space.sqft} sqft</span>
          <span>•</span>
          <span>Up to ${space.max_capacity} ppl</span>
        </div>

        <h3 class="text-base font-bold text-white group-hover:text-indigo-300 transition line-clamp-1 mb-2">
          <a href="/space/${space.id}">
            ${escapeHtml(space.title)}
          </a>
        </h3>

        <p class="text-xs text-slate-400 line-clamp-2 mb-4 flex-grow leading-relaxed">
          ${escapeHtml(space.description)}
        </p>

        <div class="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 mb-4 space-y-1.5 text-xs">
          <div class="flex items-center gap-2 text-slate-300">
            <i class="fa-solid fa-sun text-amber-400 w-4 text-center"></i>
            <span class="text-slate-400 truncate">${escapeHtml(space.ai_lighting || "Natural lighting")}</span>
          </div>
          <div class="flex items-center gap-2 text-slate-300">
            <i class="fa-solid fa-volume-xmark text-cyan-400 w-4 text-center"></i>
            <span class="text-slate-400 truncate">${escapeHtml(space.ai_noise_level || "Quiet environment")}</span>
          </div>
        </div>

        ${reasonHtml}

        <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
          <span class="text-[11px] text-slate-500 flex items-center gap-1">
            <i class="fa-solid fa-file-signature text-slate-400"></i> AI Micro-Lease
          </span>
          <a 
            href="/space/${space.id}"
            class="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold transition"
          >
            View & Book Space
          </a>
        </div>
      </div>

    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  if (!text) return "";
  let out = escapeHtml(text);
  // Bold
  out = out.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Bullet lists
  out = out.replace(/\n\* (.*?)/g, "<br>• $1");
  out = out.replace(/\n- (.*?)/g, "<br>• $1");
  // New lines
  out = out.replace(/\n/g, "<br>");
  return out;
}
