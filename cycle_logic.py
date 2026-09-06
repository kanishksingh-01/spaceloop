"""
Core cycle-phase calculation.

This is intentionally simple (average-based, not predictive ML) so it's
reliable to demo. Swap in a smarter model later if there's time.
"""
from datetime import date, timedelta


def calculate_phase(period_start: date, cycle_length: int = 28, today: date = None) -> dict:
    today = today or date.today()

    if today < period_start:
        # Logged a future date by mistake, or clock skew — treat as day 1.
        day_in_cycle = 1
    else:
        day_in_cycle = (today - period_start).days % cycle_length + 1

    if day_in_cycle <= 5:
        phase = "Menstrual"
        partner_tip = "She may be low on energy or in discomfort. Go easy, keep water/snacks handy, and check in gently."
    elif day_in_cycle <= 13:
        phase = "Follicular"
        partner_tip = "Energy is usually picking up. Good window for plans, but still worth checking how she's feeling."
    elif day_in_cycle <= 16:
        phase = "Ovulation"
        partner_tip = "Often the highest-energy phase. Mood is usually more upbeat."
    else:
        phase = "Luteal"
        partner_tip = "PMS symptoms (mood swings, cramps, fatigue) are common here. Patience and small comforts help a lot."

    cycles_elapsed = (today - period_start).days // cycle_length
    next_period_estimate = period_start + timedelta(days=cycle_length * (cycles_elapsed + 1))

    return {
        "phase": phase,
        "day_in_cycle": day_in_cycle,
        "cycle_length": cycle_length,
        "next_period_estimate": next_period_estimate.isoformat(),
        "partner_tip": partner_tip,
    }


# --- "Is this normal?" rule engine (MVP version, no LLM call needed yet) ---
# Keys are lowercase substrings to match in the free-text symptom description.
_RED_FLAG_KEYWORDS = {
    "heavy bleeding": "Soaking through a pad/tampon every hour for 2+ hours is not typical — please consider seeing a doctor.",
    "severe pain": "Pain severe enough to disrupt daily activity is worth getting checked, especially if it's new or worsening.",
    "fainting": "Fainting or dizziness with your period can have several causes and is worth medical attention.",
    "bleeding between periods": "Bleeding outside your usual cycle can happen for many reasons — a check-up can help rule things out.",
    "no period 3 months": "Missing periods for 3+ months (and not pregnant) is worth discussing with a doctor.",
    "clots larger than a coin": "Large clots can sometimes indicate heavier-than-typical flow — worth mentioning to a doctor if frequent.",
}


def check_symptom(symptom_text: str) -> dict:
    text = symptom_text.lower()
    for keyword, note in _RED_FLAG_KEYWORDS.items():
        if keyword in text:
            return {"flagged_normal": False, "note": note}

    return {
        "flagged_normal": True,
        "note": (
            "This is commonly reported and usually within the normal range. "
            "This isn't a medical diagnosis — if it worries you or persists, a doctor can give you a proper answer."
        ),
    }


# --- PCOD/PCOS risk questionnaire (MVP version) ---
# Each answer is a bool (True = symptom present). This produces a RISK
# INDICATOR only — never present this as a diagnosis in the UI or pitch.
_PCOD_QUESTIONS = [
    "irregular_periods",     # cycles longer than 35 days or fewer than 8/year
    "excess_hair_growth",    # face/chin/chest
    "acne_or_oily_skin",
    "weight_gain_unexplained",
    "hair_thinning",
    "difficulty_conceiving",
]


# --- Mood detection (MVP keyword-based fallback) ---
# TODO (stretch): replace with an LLM call (e.g. Groq) for nuance — this
# keyword version exists so the feature works end-to-end even without an API key.
_MOOD_KEYWORDS = {
    "sad": (["sad", "cry", "crying", "down", "empty", "lonely"],
            "You mentioned feeling low — this can be common in the luteal phase due to hormone shifts."),
    "anxious": (["anxious", "worried", "nervous", "stressed", "overwhelmed"],
                "You mentioned feeling anxious — stress and hormone changes often show up together."),
    "irritable": (["angry", "irritated", "annoyed", "frustrated", "snap"],
                  "You mentioned irritability — this is a very common PMS-related mood shift."),
    "tired": (["tired", "exhausted", "drained", "no energy", "fatigue"],
              "You mentioned low energy — fatigue is common around your period."),
    "happy": (["happy", "good", "great", "excited", "energetic"],
              "You're feeling good — a nice window to hold onto!"),
}


def analyze_mood(text: str) -> dict:
    lower = text.lower()
    for mood, (keywords, note) in _MOOD_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return {"mood_label": mood, "reason_note": note}
    return {"mood_label": "neutral", "reason_note": "No strong mood signal detected in this entry."}


def score_pcod_risk(answers: dict) -> dict:
    score = sum(1 for q in _PCOD_QUESTIONS if answers.get(q))
    if score <= 1:
        level = "low"
    elif score <= 3:
        level = "moderate"
    else:
        level = "high"

    return {
        "risk_score": score,
        "risk_level": level,
        "disclaimer": (
            "This is a self-reported risk indicator based on common PCOD/PCOS symptoms, "
            "not a medical diagnosis. A gynecologist visit (often with an ultrasound and "
            "blood test) is needed to actually confirm PCOD/PCOS."
        ),
    }
