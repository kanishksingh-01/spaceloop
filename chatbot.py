"""
AI companion chatbot: three blended modes in one conversation.

1. Comfort/Q&A mode (default): warm, pampering tone, answers general questions
   about periods/cycles/PCOD, casual chat, and folds in the 'is this normal?'
   symptom check when relevant.
2. Calm mode: detected from distress language ('overwhelmed', 'panicking',
   'can't breathe', etc.) — walks her through a short breathing/grounding
   exercise instead of just talking.
3. Draft mode: detected from message content ('draft a message to my boss',
   'explain to my teacher', etc.) — writes a short, polite, non-oversharing
   message the user can copy-paste.

Falls back to rule-based canned responses if no GROQ_API_KEY is set, so the
demo never breaks even without an API key configured.
"""
import requests
from cycle_logic import check_symptom

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a warm, comforting companion inside a women's health app called
Cycle Care. Talk like a caring, emotionally intelligent friend — not a clinical assistant.
Use soft, gentle language. Occasional soft emojis (🌸💛✨) are fine, but don't overdo it.

You help with:
1. General questions & reassurance: answer questions about periods, cycle phases, common
   symptoms, PCOD/PCOS basics, and general reproductive health in plain, friendly language.
   If she describes a physical symptom, respond with genuine warmth AND practical, honest
   guidance — never dismiss her, but also never diagnose. If something sounds like it could
   be serious, gently suggest seeing a doctor without alarming her. If you don't know
   something for certain, say so honestly instead of guessing.
2. Calming her down: if she sounds overwhelmed, anxious, panicked, or in distress, slow
   down and walk her through a short, simple grounding or breathing exercise step by step
   (e.g. slow breathing counts, noticing her surroundings) before anything else. Keep your
   tone very calm and unhurried here.
3. Message drafting: if she asks you to draft a message to a boss, teacher, coach, or anyone
   else explaining she needs flexibility today, write a short, polite, professional message
   that does NOT overshare medical details. Keep it copy-paste ready.

Keep replies short — 2-5 sentences — unless you're walking through a calming exercise or
drafting a message, where a little more structure is fine. Always make her feel heard before
giving information or advice.
"""

_DRAFT_KEYWORDS = [
    "draft a message", "draft message", "write a message", "message to my boss",
    "message to my teacher", "tell my teacher", "tell my boss", "explain to my",
    "excuse for", "need flexibility", "need an extension",
]

_DISTRESS_KEYWORDS = [
    "overwhelmed", "panicking", "panic attack", "can't breathe", "cant breathe",
    "freaking out", "spiraling", "spiralling", "can't calm down", "cant calm down",
    "so anxious", "really anxious", "scared", "losing it",
]

_FAQ_KEYWORDS = {
    "why do i get cramps": (
        "Cramps happen because your uterus contracts to shed its lining, and those "
        "contractions can briefly cut off a bit of blood/oxygen to the muscle, which is "
        "what causes the pain. A heating pad, gentle movement, or ibuprofen (if it agrees "
        "with you) can help."
    ),
    "how long should a period last": (
        "Most periods last somewhere between 2 and 7 days — that's a wide but normal range. "
        "If yours is consistently much longer or shorter than that, it's worth mentioning to "
        "a doctor."
    ),
    "is spotting normal": (
        "Light spotting between periods can happen for a few reasons — ovulation, "
        "starting/stopping birth control, or stress — and is often harmless. If it happens "
        "often or with pain, it's worth getting checked."
    ),
    "what is pcod": (
        "PCOD/PCOS is a hormonal condition that can cause irregular periods, acne, excess "
        "hair growth, or weight changes. It's manageable with the right diagnosis and care — "
        "a doctor can confirm it with a simple exam and sometimes an ultrasound or blood test."
    ),
}


def is_draft_request(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _DRAFT_KEYWORDS)


def is_distress(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _DISTRESS_KEYWORDS)


_CALMING_EXERCISE = (
    "Let's slow down together for a moment. 🌸\n\n"
    "Breathe in slowly for 4 counts... hold for 4... and breathe out for 6.\n\n"
    "Now look around and name 3 things you can see, 2 things you can hear, and 1 thing "
    "you can feel (like your feet on the floor). You're safe right now — this feeling will pass."
)


def _fallback_reply(user_text: str, mode: str) -> str:
    if mode == "calm":
        return _CALMING_EXERCISE
    if mode == "draft":
        return (
            "Here's a draft you can copy: \u201cHi, I'm not feeling 100% today and could use "
            "a bit of flexibility — I'll make sure everything is caught up. Thanks for "
            "understanding.\u201d 🌸"
        )
    lower = user_text.lower()
    for question, answer in _FAQ_KEYWORDS.items():
        if question in lower:
            return answer
    result = check_symptom(user_text)
    prefix = "That sounds tough. " if not result["flagged_normal"] else "Totally hear you. "
    return prefix + result["note"] + " 💛"


def _build_context(phase_info: dict | None) -> str:
    if not phase_info:
        return ""
    return (
        f"\n\nContext: she is on day {phase_info['day_in_cycle']} of her cycle, "
        f"currently in the {phase_info['phase']} phase."
    )


def chat_reply(user_text: str, phase_info: dict = None, api_key: str = "") -> dict:
    if is_distress(user_text):
        mode = "calm"
    elif is_draft_request(user_text):
        mode = "draft"
    else:
        mode = "comfort"

    if not api_key:
        return {"reply": _fallback_reply(user_text, mode), "mode": mode, "source": "fallback"}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + _build_context(phase_info)},
        {"role": "user", "content": user_text},
    ]
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 350, "temperature": 0.8},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
        return {"reply": reply, "mode": mode, "source": "groq"}
    except Exception as e:
        fallback = _fallback_reply(user_text, mode)
        return {"reply": fallback, "mode": mode, "source": "fallback", "error": str(e)}

