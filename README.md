# Cycle Care & Partner Connect

A cycle-tracking app with a built-in partner-connect feature — so the people
who care about you can stay gently informed without you having to explain
everything every time.

## Features (MVP)

- Cycle tracking with phase calculation (Menstrual / Follicular / Ovulation / Luteal)
- "Is this normal?" symptom checker with red-flag detection
- PCOD/PCOS self-assessment (risk indicator, not a diagnosis)
- Partner connect via a unique mutual code
- Partner dashboard + phase-change notifications
- Comforting onboarding screen

## Tech stack

- Backend: Flask + Flask-SQLAlchemy
- Database: SQLite (swap `SQLALCHEMY_DATABASE_URI` in `config.py` for Postgres later)
- Frontend: server-rendered templates for now; can be swapped for React

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

App runs at `http://localhost:5000`.

## API quick reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/register` | POST | Create a user (`role`: `self` or `partner`) |
| `/api/login` | POST | Login |
| `/api/partner/link` | POST | Redeem a connect code to link accounts |
| `/api/cycle/log` | POST | Log a period start date |
| `/api/cycle/phase/<user_id>` | GET | Get current phase |
| `/api/symptom/check` | POST | "Is this normal?" check |
| `/api/pcod/assess` | POST | PCOD/PCOS risk questionnaire |
| `/api/notifications/<user_id>` | GET | Partner's notifications |
| `/api/journal/add` | POST | Add a journal entry (mood detection is a stretch goal, not yet wired) |

## Important framing note

Everything under "PCOD/PCOS" and "is this normal" is a **self-reported risk
indicator / informational tool**, not a medical diagnosis. Keep this framing
in the UI copy and in the pitch — it's both more honest and safer.

## AI usage disclosure

This starter scaffold (project structure, models, rule-based symptom/PCOD
logic, and this README) was generated with the help of Claude (Anthropic),
per Hack2Ignite rule 2 ("Use of AI is allowed, teams must disclose usage of
AI in PPT / GitHub readme"). All further development happens live during the
48-hour window — update this section with anything else the team uses AI for
(e.g. the mood-detection LLM call, if added).
