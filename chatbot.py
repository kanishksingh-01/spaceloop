import os
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def detect_mode(user_text: str, requested_mode: Optional[str] = None) -> str:
    """Detects whether user needs comfort, guided calm/breathing, draft email, or Q&A."""
    if requested_mode in ["comfort", "calm", "draft", "qa"]:
        return requested_mode

    t = user_text.lower()
    if any(w in t for w in ["panic", "can't breathe", "anxious", "overwhelmed", "grounding", "breathe", "calm me", "scared"]):
        return "calm"
    if any(w in t for w in ["draft", "email", "message to boss", "tell my teacher", "excuse", "leave note", "sick leave", "manager", "reschedule"]):
        return "draft"
    if any(w in t for w in ["why", "what is", "can i", "is it possible", "how does", "hormone", "ovulation", "pcod", "pcos"]):
        return "qa"

    return "comfort"


def chat_reply(user_text: str, phase_info: Optional[Dict[str, Any]] = None, api_key: Optional[str] = None, requested_mode: Optional[str] = None, companion_name: str = "Aura") -> Dict[str, Any]:
    """
    Produces an empathetic, multi-mode AI companion response using Groq with offline fallback.
    """
    mode = detect_mode(user_text, requested_mode)
    comp_name = companion_name.strip() if companion_name else "Aura"
    
    # Try calling Groq if API key is present
    if api_key:
        try:
            return _call_groq_api(user_text, phase_info, api_key, mode, comp_name)
        except Exception as e:
            logger.warning("Groq API call encountered an issue; falling back gracefully: %s", e)

    return _fallback_reply(user_text, phase_info, mode, comp_name)


def _call_groq_api(user_text: str, phase_info: Optional[Dict[str, Any]], api_key: str, mode: str, companion_name: str = "Aura") -> Dict[str, Any]:
    phase_ctx = ""
    if phase_info:
        phase_ctx = (f"User's current cycle context: Phase is {phase_info.get('phase')}, "
                     f"Day {phase_info.get('day_in_cycle')} of {phase_info.get('cycle_length')}. "
                     f"Biorhythm state: {phase_info.get('energy_forecast')}.")

    system_prompt = f"""You are '{companion_name}', a warm, deeply empathetic, and scientifically grounded women's health companion inside Cycle Care.
{phase_ctx}

Behavior guidelines:
1. Tone: Warm, validating, deeply comforting, and respectful. Never clinical, patronizing, or dismissive.
2. In 'calm' mode: Guide the user through calming grounding (4-7-8 breathing or 5-4-3-2-1 sensory grounding) with brief, peaceful sentences.
3. In 'draft' mode: Create a polite, concise, professional message she can copy-paste to a boss, teacher, or team to request flexibility or rest due to feeling unwell, WITHOUT oversharing private medical details.
4. In 'qa' mode: Give clear, evidence-based reproductive science explanations with compassionate advice.
5. In 'comfort' mode: Validate her emotions first, offer practical comfort (warmth, hydration, gentle movement), and remind her that her feelings are completely valid.
6. Keep responses conversational, concise (2-4 paragraphs max), and easy to read on mobile.
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.7,
        "max_tokens": 450
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=7)
    if resp.status_code == 200:
        data = resp.json()
        reply_text = data["choices"][0]["message"]["content"].strip()
        return {
            "reply": reply_text,
            "mode": mode,
            "trigger_breathing": (mode == "calm")
        }
    else:
        logger.error("Groq returned status %s: %s", resp.status_code, resp.text)
        return _fallback_reply(user_text, phase_info, mode, companion_name)


def _fallback_reply(user_text: str, phase_info: Optional[Dict[str, Any]], mode: str, companion_name: str = "Aura") -> Dict[str, Any]:
    """
    Rich offline fallback ensuring flawless demo and offline resilience.
    """
    phase_str = phase_info.get("phase") if phase_info else "current"
    t = user_text.lower()

    if mode == "calm":
        reply = (
            "Take a gentle breath with me right now. You are safe, and this moment will pass.\n\n"
            "Let's do a 4-7-8 rhythm together:\n"
            "• Inhale quietly through your nose for 4 counts...\n"
            "• Hold that breath gently for 7 counts...\n"
            "• Slowly release with a whoosh for 8 counts.\n\n"
            "Drop your shoulders, unclamp your jaw, and let your hands rest softly. I'm right here with you."
        )
        return {"reply": reply, "mode": "calm", "trigger_breathing": True}

    if mode == "draft":
        reply = (
            "Here is a discreet, professional draft you can copy and send:\n\n"
            "\"Hi [Name],\n\n"
            "I am feeling somewhat under the weather today and would like to request permission to [work from home / take personal leave / reschedule our afternoon meeting]. "
            "I'll ensure urgent tasks are covered and will check in as soon as I'm back on track.\n\n"
            "Thank you for understanding,\n[Your Name]\"\n\n"
            "Feel free to tweak the bracketed parts. It keeps your health completely private while maintaining full professional courtesy."
        )
        return {"reply": reply, "mode": "draft", "trigger_breathing": False}

    if mode == "qa":
        if "pcod" in t or "pcos" in t:
            reply = (
                "PCOD/PCOS is a common endocrine and metabolic variation where the ovaries produce slightly higher androgens, "
                "often leading to irregular cycles, ovulatory delays, and insulin sensitivity. "
                "It responds wonderfully to circadian rhythm care, protein-rich balanced meals, resistance training, and stress reduction. "
                "You can also use our 'PCOD Check' tab for a guided risk evaluation!"
            )
        elif "cramp" in t or "pain" in t:
            reply = (
                "Period cramps (dysmenorrhea) happen when your uterine lining releases prostaglandins, triggering muscle contractions to shed the lining. "
                "Heat therapy (a warm bath or heating pad) increases blood flow and relaxes the muscles just as effectively as mild pain relievers. "
                "Magnesium glycinate and ginger tea are also powerful natural supports."
            )
        elif "luteal" in t or "pms" in t:
            reply = (
                "During your Luteal phase, progesterone peaks to nourish the uterine lining and then suddenly drops if pregnancy hasn't occurred. "
                "This hormonal dip temporarily lowers serotonin (the feel-good neurotransmitter) and increases metabolic burn by ~100-300 kcal/day! "
                "That's why cravings for carbs and emotional sensitivity are completely biological, not a lack of willpower."
            )
        else:
            reply = (
                f"You're currently in your {phase_str} phase. Your hormonal landscape influences energy, digestion, and mood across the month. "
                "What specific question or symptom would you like to explore deeper?"
            )
        return {"reply": reply, "mode": "qa", "trigger_breathing": False}

    # Default: Comfort mode
    if any(w in t for w in ["cramp", "hurts", "pain", "ache", "sore"]):
        reply = (
            "I'm so sorry you're hurting right now. Uterine contractions can be truly exhausting. "
            "Please grab a warm heating pad or hot water bottle, curl into a cozy position, and sip some warm chamomile or peppermint tea. "
            "Give yourself permission to do the bare minimum today—your body is doing intense physical work."
        )
    elif any(w in t for w in ["sad", "cry", "lonely", "hate myself", "down", "low"]):
        reply = (
            "I hear you, and I want to remind you that whatever you're feeling right now is completely valid. "
            "Hormonal shifts can feel like a heavy fog that makes everything feel sharper or more overwhelming. "
            "You don't have to fix everything today. Just wrap yourself in a soft blanket and be gentle with yourself."
        )
    elif any(w in t for w in ["tired", "exhausted", "sleepy", "burnout"]):
        reply = (
            f"Honor that tiredness. In your {phase_str} phase, your body's energy naturally shifts inward. "
            "Rest isn't something you have to earn—it's essential care. If you can take a 20-minute rest or close your eyes without guilt, please do."
        )
    else:
        reply = (
            f"I'm right here with you. During your {phase_str} phase, tuning into what your body asks for—whether that's quiet time, nourishing comfort food, or a listening ear—is the greatest form of self-care. "
            "How can I support you right now?"
        )

    return {"reply": reply, "mode": "comfort", "trigger_breathing": False}


def get_partner_tip(user_text: str, mode: str) -> Optional[str]:
    """
    Strict privacy preservation: Derives an actionable, compassionate tip for the partner
    WITHOUT ever exposing the user's raw chat message or diary entry.
    """
    t = user_text.lower()

    if mode == "calm" or any(w in t for w in ["panic", "anxious", "overwhelm", "cry", "scared"]):
        return "She is experiencing high stress or emotional overwhelm right now. A gentle hug, a quiet environment, and reassurance without asking too many questions would mean everything."

    if any(w in t for w in ["cramp", "pain", "hurts", "ache", "stomach"]):
        return "She is dealing with physical cramps or discomfort. Consider bringing her a warm heating pad, a cup of herbal tea, or handling dinner tonight."

    if any(w in t for w in ["tired", "exhausted", "sleepy", "drained"]):
        return "Her energy battery is running low. Giving her quiet space to nap and taking small chores off her plate will be deeply appreciated."

    if any(w in t for w in ["sad", "down", "lonely", "upset"]):
        return "She's having an emotionally tender day. Send a loving check-in text or surprise her with her favorite snack—no problem-solving needed, just warmth."

    if any(w in t for w in ["craving", "chocolate", "sweet", "hungry"]):
        return "A sweet treat or comfort snack would make her smile today!"

    return None


def generate_partner_chat_summary(messages: list, phase_info: Optional[Dict[str, Any]] = None, user_name: str = "She", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Produces a compassionate, privacy-safe executive briefing for the partner
    summarizing recent interactions with the AI companion.
    Never exposes raw conversation transcripts or sensitive personal secrets.
    """
    phase_str = phase_info.get("phase", "current") if phase_info else "current"
    name = user_name if user_name and user_name.strip() else "She"

    if not messages:
        return {
            "summary": f"No recent distress or special requests recorded. {name} is navigating her {phase_str} phase smoothly and peacefully.",
            "tone": "Peaceful & Steady",
            "action_nudge": "Send a sweet check-in note or ask how her day is going with gentle attention.",
            "recommended_action": "sweet_treat",
            "action_label": "Send Sweet Treat 🍫",
            "has_recent_activity": False,
            "message_count": 0
        }

    # Extract user-side texts and modes
    user_texts = [m["text"] for m in messages if m.get("sender") == "user"]
    modes = [m.get("mode", "comfort") for m in messages]
    combined_user_text = " ".join(user_texts).lower()

    # Rule-based synthesis with deep empathy & high accuracy
    if any(w in combined_user_text for w in ["cramp", "pain", "hurts", "ache", "stomach", "pelvic", "bleed"]):
        tone = "Physical Discomfort / Cramps"
        summary = f"{name} recently checked in with her companion about cramps and bodily aches during her {phase_str} phase. She appreciated comfort advice and is taking time to rest."
        action_nudge = "Bring a warm heating pad or hot water bottle, brew some herbal tea, and take care of dinner tonight."
        rec_action = "heat_pack"
        rec_label = "Send Virtual Heat Pack 🔥"
    elif "calm" in modes or any(w in combined_user_text for w in ["anxious", "panic", "overwhelm", "stressed", "scared", "can't breathe"]):
        tone = "Emotional Overwhelm / High Stress"
        summary = f"{name} utilized the companion's 4-7-8 Calm Mode for guided breathing and sensory grounding to work through emotional tension and stress."
        action_nudge = "Give her a quiet, loving hug without asking too many questions. Keep the evening calm and low-pressure."
        rec_action = "gentle_hug"
        rec_label = "Send Gentle Hug 🫂"
    elif any(w in combined_user_text for w in ["tired", "exhausted", "sleepy", "drained", "burnout"]):
        tone = "Low Energy / Rest-Seeking"
        summary = f"{name}'s energy battery is running low right now in her {phase_str} phase. Her body is expending more metabolic energy and signaling a need for recovery."
        action_nudge = "Encourage an early bedtime, keep the home environment quiet, and take small chores off her plate."
        rec_action = "warm_tea"
        rec_label = "Send Calming Tea 🍵"
    elif "draft" in modes or any(w in combined_user_text for w in ["draft", "leave", "boss", "manager", "sick note", "reschedule"]):
        tone = "Seeking Rest & Flexibility"
        summary = f"{name} used Draft Mode to politely request workplace or study flexibility so she can honor her body's need for rest."
        action_nudge = "Reassure her that prioritizing rest is healthy, and ensure she has a cozy, relaxing environment at home."
        rec_action = "dinner_taken_care"
        rec_label = "Send Dinner Handled 🍲"
    elif any(w in combined_user_text for w in ["sad", "cry", "lonely", "down", "low", "tear"]):
        tone = "Emotionally Sensitive & Tender"
        summary = f"{name} had an emotionally tender moment today. Hormonal shifts can magnify feelings of vulnerability, and she sought gentle reassurance."
        action_nudge = "Validate her feelings without jumping straight to problem-solving. Surprise her with a comfort snack or sweet check-in."
        rec_action = "sweet_treat"
        rec_label = "Send Sweet Treat 🍫"
    else:
        tone = "Balanced & Cheerful"
        summary = f"{name} had a warm, positive check-in with her companion today. She is navigating her {phase_str} phase with balance."
        action_nudge = "Celebrate her good mood! Great time to plan a fun dinner, talk about shared dreams, or enjoy a walk together."
        rec_action = "sweet_treat"
        rec_label = "Send Sweet Treat 🍫"

    return {
        "summary": summary,
        "tone": tone,
        "action_nudge": action_nudge,
        "recommended_action": rec_action,
        "action_label": rec_label,
        "has_recent_activity": True,
        "message_count": len(user_texts)
    }


