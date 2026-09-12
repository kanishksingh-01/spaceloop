import math
from datetime import datetime, date, timedelta
from typing import Dict, Any, List


def calculate_phase(period_start: date, cycle_length: int = 28) -> Dict[str, Any]:
    """
    Calculates detailed cycle phase, hormone trends, and personalized biorhythm advice.
    """
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, "%Y-%m-%d").date()

    today = date.today()
    elapsed_days = (today - period_start).days

    # Normalize to current cycle
    if elapsed_days < 0:
        day_in_cycle = 1
    else:
        day_in_cycle = (elapsed_days % cycle_length) + 1

    days_until_next = cycle_length - day_in_cycle
    next_period_date = today + timedelta(days=days_until_next)

    # Dynamic phase boundaries based on cycle length
    # Default 28-day: Menstrual (1-5), Follicular (6-13), Ovulation (14-16), Luteal (17-28)
    ovulation_day = cycle_length - 14
    menstrual_end = min(5, max(3, int(cycle_length * 0.18)))
    ovulation_start = max(menstrual_end + 1, ovulation_day - 1)
    ovulation_end = min(cycle_length - 2, ovulation_day + 2)

    if day_in_cycle <= menstrual_end:
        phase = "Menstrual"
        phase_desc = "Inner Winter: Hormones at baseline, body shedding lining."
        energy_forecast = "Lower physical energy, introspective and reflective."
        nutrition_tip = "Iron-rich foods (spinach, lentils, dark cocoa), vitamin C, and warm herbal teas to replenish lost minerals."
        workout_tip = "Restorative yoga, gentle walking, light stretching. Honor your body's need for slower pace."
        partner_tip = "Her energy is naturally low and cramps might be present. A hot water bottle, warm blanket, and zero pressure to be socially active mean the world right now."
        fertility_status = "Low"
    elif day_in_cycle < ovulation_start:
        phase = "Follicular"
        phase_desc = "Inner Spring: Estrogen on the rise, follicle maturing."
        energy_forecast = "Rising energy, renewed mental clarity, creative focus."
        nutrition_tip = "Fermented foods (kombucha, kimchi), sprouted grains, lean protein, and seeds (flax & pumpkin for seed cycling)."
        workout_tip = "Cardio, dynamic strength training, group fitness. Great time to try new workouts as endurance peaks."
        partner_tip = "She is feeling energized and optimistic! Great time for social dates, brainstorming projects, and trying fun activities together."
        fertility_status = "Moderate (approaching fertile window)"
    elif day_in_cycle <= ovulation_end:
        phase = "Ovulation"
        phase_desc = "Inner Summer: LH surge and estrogen peak, egg is released."
        energy_forecast = "Peak vitality, high confidence, strong social magnetism."
        nutrition_tip = "Anti-inflammatory and antioxidant-rich foods: berries, cruciferous vegetables (broccoli), and lots of hydration to support liver clearance of estrogen."
        workout_tip = "High-Intensity Interval Training (HIIT), peak strength sessions, power flow yoga."
        partner_tip = "Her vitality and communication drive are at their monthly high. Be attentive, present, and enjoy deep conversations."
        fertility_status = "Peak (Highest chance of conception)"
    else:
        phase = "Luteal"
        phase_desc = "Inner Autumn: Progesterone rises to support potential pregnancy, then drops."
        energy_forecast = "Variable energy, higher metabolic burn, heightened emotional sensitivity."
        nutrition_tip = "Magnesium-rich foods (pumpkin seeds, avocado, dark chocolate), complex carbs (sweet potatoes, oats), and vitamin B6 to curb PMS cravings."
        workout_tip = "Moderate Pilates, steady-state swimming, light resistance. Avoid overexertion if feeling fatigued."
        partner_tip = "Progesterone is dropping, which can cause sudden mood shifts, bloating, and fatigue. Be extra patient, offer a surprise treat or warm cup of tea, and validate her feelings without offering unsolicited solutions."
        fertility_status = "Low (Post-ovulation)"

    fertile_start = max(1, ovulation_day - 4)
    fertile_end = min(cycle_length, ovulation_day + 1)

    return {
        "day_in_cycle": day_in_cycle,
        "cycle_length": cycle_length,
        "phase": phase,
        "phase_desc": phase_desc,
        "days_until_next": days_until_next,
        "next_period_estimate": next_period_date.strftime("%B %d, %Y"),
        "fertile_window": f"Day {fertile_start} – Day {fertile_end}",
        "fertility_status": fertility_status,
        "energy_forecast": energy_forecast,
        "nutrition_tip": nutrition_tip,
        "workout_tip": workout_tip,
        "partner_tip": partner_tip,
        "progress_pct": int((day_in_cycle / cycle_length) * 100),
    }


def get_hormone_curves(day_in_cycle: int, cycle_length: int = 28) -> Dict[str, Any]:
    """
    Generates normalized hormone level curves (0 to 100) for Estrogen, Progesterone, LH, and FSH.
    Returns both the day-by-day series for charts and today's current values.
    """
    days = list(range(1, cycle_length + 1))
    estrogen_curve = []
    progesterone_curve = []
    lh_curve = []
    fsh_curve = []

    ovulation_day = cycle_length - 14

    for d in days:
        # Estrogen: bimodal curve peaking before ovulation and mid-luteal
        e1 = 80 * math.exp(-0.5 * ((d - (ovulation_day - 1)) / 2.2) ** 2)
        e2 = 50 * math.exp(-0.5 * ((d - (ovulation_day + 7)) / 3.0) ** 2)
        e = min(100, int(15 + e1 + e2))
        estrogen_curve.append(e)

        # Progesterone: low before ovulation, single high bell in luteal
        p_peak = ovulation_day + 7
        if d < ovulation_day:
            p = int(5 + 3 * (d / ovulation_day))
        else:
            p_val = 85 * math.exp(-0.5 * ((d - p_peak) / 3.2) ** 2)
            p = min(100, int(8 + p_val))
        progesterone_curve.append(p)

        # LH: sharp surge right at ovulation
        lh_val = 90 * math.exp(-0.5 * ((d - ovulation_day) / 1.0) ** 2)
        lh = min(100, int(10 + lh_val))
        lh_curve.append(lh)

        # FSH: bump in early follicular and smaller spike at ovulation
        fsh1 = 30 * math.exp(-0.5 * ((d - 3) / 2.0) ** 2)
        fsh2 = 45 * math.exp(-0.5 * ((d - ovulation_day) / 1.2) ** 2)
        fsh = min(100, int(12 + fsh1 + fsh2))
        fsh_curve.append(fsh)

    current_idx = max(0, min(len(days) - 1, day_in_cycle - 1))

    return {
        "days": days,
        "estrogen_series": estrogen_curve,
        "progesterone_series": progesterone_curve,
        "lh_series": lh_curve,
        "fsh_series": fsh_curve,
        "today_levels": {
            "estrogen": estrogen_curve[current_idx],
            "progesterone": progesterone_curve[current_idx],
            "lh": lh_curve[current_idx],
            "fsh": fsh_curve[current_idx],
        }
    }


def check_symptom(symptom_text: str) -> Dict[str, Any]:
    """
    Intelligent symptom triage engine with red-flag detection and clinical reassurance.
    """
    s = symptom_text.lower()

    # Red-flag urgent patterns
    urgent_triggers = [
        "soaking through", "fever and foul", "unbearable pelvic", "fainting",
        "passed out", "throwing up uncontrollably", "extreme sharp pain",
        "soaking a pad an hour", "bleeding between periods for months", "severe vomiting"
    ]
    for trigger in urgent_triggers:
        if trigger in s:
            return {
                "flagged_normal": False,
                "severity": "urgent",
                "category": "Immediate Medical Evaluation Recommended",
                "note": "This symptom pattern requires prompt evaluation by a gynecologist or urgent care provider. Extreme pain, hemorrhage (soaking through a pad/tampon every 1-2 hours), or fever with pelvic pain can indicate ectopic pregnancy, acute infection, or severe ovarian cyst complication.",
                "remedy": "Do not wait. Contact your healthcare professional or local emergency health triage service.",
                "disclaimer": "This automated triage is informational and does not constitute medical diagnosis or replace emergency care."
            }

    # Monitor closely patterns
    monitor_triggers = [
        "clots larger than", "heavy flow", "missed 2 periods", "spotting after intercourse",
        "chronic constipation", "sharp pain on one side", "dizzy", "fatigue for weeks"
    ]
    for trigger in monitor_triggers:
        if trigger in s:
            return {
                "flagged_normal": False,
                "severity": "monitor",
                "category": "Worth Monitoring & Discussing With Doctor",
                "note": "While occasional variations occur, symptoms like persistent spotting, large clots (>quarter size), or severe fatigue warrant tracking and mentioning at your next annual gynecological appointment.",
                "remedy": "Log the frequency, duration, and pain score in your journal. Keep well hydrated with electrolytes and monitor if it worsens.",
                "disclaimer": "Informational check only. Always consult a licensed doctor for ongoing or worsening symptoms."
            }

    # Common physiological symptoms
    reassurance_map = [
        (["cramp", "pain", "ache", "backache"], "Mild to moderate cramping (dysmenorrhea) is caused by uterine prostaglandins contracting to shed the lining. This is very common.", "Apply a warm heating pad, take magnesium glycinate, sip ginger/chamomile tea, and try light pelvic stretches."),
        (["bloat", "gas", "water"], "Bloating is driven by fluctuations in progesterone and estrogen affecting fluid retention and digestion. Very typical in the late luteal and early menstrual phases.", "Increase potassium intake (bananas, coconut water), stay hydrated to reduce water retention, and reduce sodium."),
        (["mood", "crying", "anxious", "sad", "irritable", "temper"], "Hormonal shifts, particularly the drop in progesterone and serotonin just before menstruation, commonly cause emotional sensitivity and irritability.", "Practice gentle self-compassion, engage in the Calm Mode breathing guide, get 8 hours of rest, and limit caffeine."),
        (["tender", "breast", "sore"], "Breast tenderness (mastalgia) occurs as progesterone rises post-ovulation, causing milk duct tissue to temporarily swell.", "Wear a supportive, non-wired cotton bra and reduce excess salt and caffeine."),
        (["acne", "breakout", "pimple", "oily"], "Luteal phase androgen dominance stimulates sebum production, leading to hormonal breakouts along the jawline and chin.", "Use gentle salicylic acid cleanser, avoid picking, and prioritize zinc and hydration."),
        (["tired", "exhaust", "sleepy", "low energy"], "Natural drop in metabolic and hormonal drive in the menstrual or late luteal phase.", "Prioritize 15-minute power rests, sleep 8+ hours, and increase iron and complex carbohydrates.")
    ]

    for keywords, note, remedy in reassurance_map:
        if any(kw in s for kw in keywords):
            return {
                "flagged_normal": True,
                "severity": "normal",
                "category": "Common Physiological Cycle Variation",
                "note": note,
                "remedy": remedy,
                "disclaimer": "Informational check only. If symptoms persist or become severe, consult your doctor."
            }

    return {
        "flagged_normal": True,
        "severity": "normal",
        "category": "General Observation",
        "note": "Your symptom appears within general physiological norms, but your body's rhythm is unique. Continue logging changes to build your cycle baseline.",
        "remedy": "Stay hydrated, prioritize restful sleep, and track how this symptom correlates with your cycle phase.",
        "disclaimer": "Informational check only. Consult a healthcare professional if you have concerns."
    }


def score_pcod_risk(answers: Dict[str, bool]) -> Dict[str, Any]:
    """
    Evaluates PCOD/PCOS risk using evidence-based self-reported clinical markers
    grounded in the Rotterdam Criteria (ovulatory dysfunction, hyperandrogenism, metabolic indicators).
    """
    weights = {
        "irregular_periods": 3,       # Hall-mark criterion: oligo/anovulation
        "excess_hair_growth": 2,      # Hyperandrogenism (hirsutism)
        "acne_or_oily_skin": 1,       # Androgenic symptom
        "weight_gain_unexplained": 2, # Insulin resistance / metabolic factor
        "hair_thinning": 2,           # Androgenic alopecia
        "difficulty_conceiving": 2,   # Subfertility / anovulatory marker
        "pelvic_pain_chronic": 1,     # Secondary symptom
        "family_history": 2,          # Strong genetic linkage
    }

    total_possible = sum(weights.values())
    score = 0
    flagged_keys = []

    for key, weight in weights.items():
        if answers.get(key, False):
            score += weight
            flagged_keys.append(key)

    if score <= 3:
        risk_level = "low"
        summary = "Low Risk Profile. Your symptoms do not strongly match the Rotterdam criteria for Polycystic Ovary Syndrome."
        guidance = "Maintain balanced circadian sleep, whole-food nutrition, and routine wellness checkups."
    elif score <= 7:
        risk_level = "moderate"
        summary = "Moderate Risk Profile. You reported some hallmark symptoms associated with hormonal imbalance or insulin sensitivity."
        guidance = "Consider getting baseline bloodwork (fasting insulin, LH:FSH ratio, total testosterone, and DHEA-S) with a gynecologist or endocrinologist."
    else:
        risk_level = "elevated"
        summary = "Elevated Risk Profile. You have multiple clinical indicators strongly aligned with PCOD/PCOS."
        guidance = "We strongly recommend scheduling a pelvic ultrasound and comprehensive metabolic/hormonal panel with your doctor. Early lifestyle interventions and targeted care can dramatically improve symptoms."

    return {
        "risk_score": score,
        "max_score": total_possible,
        "risk_level": risk_level,
        "summary": summary,
        "guidance": guidance,
        "flagged_count": len(flagged_keys),
        "doctor_checklist": [
            "Request a pelvic ultrasound (checking for polycystic ovarian morphology)",
            "Check hormonal profile (Free & Total Testosterone, LH, FSH, Estradiol)",
            "Evaluate metabolic markers (Fasting blood glucose, fasting insulin, HbA1c)",
            "Screen for thyroid function (TSH, Free T3/T4) and Prolactin to rule out overlaps"
        ],
        "disclaimer": "This questionnaire is an educational self-assessment indicator and explicitly NOT a medical diagnosis. Only a licensed physician can diagnose PCOD or PCOS."
    }


def analyze_mood(text: str) -> Dict[str, Any]:
    """
    Classifies mood and psychological state from private journal entries.
    """
    t = text.lower()
    
    if any(w in t for w in ["happy", "grateful", "amazing", "great", "energetic", "excited", "radiant", "productive"]):
        return {"mood_label": "Radiant & Energized", "reason_note": "Positive and empowered outlook detected."}
    elif any(w in t for w in ["calm", "peace", "relaxed", "fine", "content", "okay", "good", "balanced"]):
        return {"mood_label": "Peaceful & Grounded", "reason_note": "Steady and calm mental space."}
    elif any(w in t for w in ["cry", "sad", "down", "lonely", "weep", "tender", "vulnerable", "soft"]):
        return {"mood_label": "Emotionally Sensitive", "reason_note": "Heightened tenderness, natural in late luteal/menstrual."}
    elif any(w in t for w in ["angry", "irritat", "mad", "annoy", "frustrat", "rage", "snapped"]):
        return {"mood_label": "Irritable & Stressed", "reason_note": "Elevated tension or hormonal mood dip."}
    elif any(w in t for w in ["tired", "exhaust", "sleepy", "drained", "no energy", "burnout"]):
        return {"mood_label": "Fatigued & Rest-Seeking", "reason_note": "Physical and emotional battery is low."}
    elif any(w in t for w in ["anxious", "panic", "worry", "overwhelm", "scared", "fear", "racing"]):
        return {"mood_label": "Anxious & Overwhelmed", "reason_note": "Heightened anxiety; grounding suggested."}

    return {"mood_label": "Reflective & Centered", "reason_note": "Thoughtful self-expression."}
