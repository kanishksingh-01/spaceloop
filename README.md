# SpaceLoop 🌀

> **AI-powered platform that converts unused property spaces into useful, affordable temporary spaces by intelligently matching owners with people who need them.**

Built for **Hack2Ignite 2026**.

---

## 💡 The Problem

In every city, hundreds of millions of square feet sit vacant or severely underutilized:
- **Empty Garages & Basements:** Sitting vacant during the day while owners pay property taxes.
- **Driveways & Curbs:** Empty while commuters and EV drivers circle the block searching for parking.
- **Off-Peak Cafés & Retail:** Closed after 4 PM with zero revenue generation.
- **Vacant Storefronts:** Trapped in multi-year lease limbo.

Meanwhile, **creators, students, remote workers, and micro-entrepreneurs** are priced out of exorbitant commercial leases ($400+/day photo studios, rigid storage facilities, and expensive coworking spaces).

---

## 🚀 The SpaceLoop Solution

SpaceLoop unlocks urban "dead space" as flexible, liquid temporary rentals (by the hour or day) powered by 4 key AI capabilities:

```mermaid
flowchart LR
    A[Host Snaps Photo / Enters Notes] --> B[AI Visual Space Inspector]
    B --> C[Auto-Generated Dimensions, Amenities & Dynamic Price]
    C --> D[Active Marketplace Listing]
    E[Renter Natural Language Query] --> F[AI Matchmaking & Compatibility Score]
    D --> F
    F --> G[1-Click Booking + Automated AI Micro-Lease]
```

### 1. 🤖 Multimodal AI Space Inspector
Hosts don't fill tedious forms. Upload a photo and describe rough notes:
- Vision & LLM models estimate **usable square footage**, **ambient natural lighting quality**, and **acoustic background noise profile (<36 dB)**.
- Detects electrical outlets (e.g. *Dedicated 20A grounded circuits*), access points, and safety flags.
- Auto-generates a high-converting listing title, amenities checklist, and marketing copy.

### 2. 🎯 Natural Language Intent Matchmaker
Renters search in conversational plain English:
> *"Looking for a quiet, sunlit space for a 3-person podcast recording on Saturday afternoon with power outlets under $40/hr"*
- The matching engine parses acoustic needs, capacity, lighting, and implied budgets.
- Ranks candidate spaces with a **0–100% Compatibility Score** and breaks down exact pros/cons.

### 3. 🛡️ Automated AI Micro-Lease Agreements
Property owners hesitate to rent because of tenancy laws and property liability.
- SpaceLoop synthesizes an enforceable, plain-English **Temporary Space Use License Agreement** on every booking.
- Contains revocable license terms (no tenancy created), activity-tailored house rules, noise curfews, mutual indemnification, and check-out clean-up checklists.

### 4. 📈 Dynamic Micro-Pricing & Revenue Calculator
- Real-time calculator estimating hourly and daily rates based on local density and square footage.
- Visualizes projected monthly/annual passive income (average hosts earn **$1,200/mo**).

### 5. 💬 LoopBot AI Concierge
- Embedded floating AI assistant that assists renters with space suitability and advises hosts on staging and pricing.

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask 3.0, Flask-SQLAlchemy, SQLite
- **AI Engine:** Dual-provider architecture supporting **Groq** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) and **Google Gemini** (`gemini-1.5-flash`), backed by a reliable rule-based heuristic fallback engine for offline or rate-limited environments.
- **Frontend:** Tailwind CSS, JetBrains Mono, FontAwesome 6, Vanilla JS.

---

## ⚡ Quick Start

```bash
# 1. Clone repository
git clone https://github.com/kanishksingh-01/hack2ignite-practice.git
cd hack2ignite

# 2. Activate virtual environment
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set AI Keys for live cloud LLM inference
export GROQ_API_KEY="your-groq-key"
export GEMINI_API_KEY="your-gemini-key"

# 5. Run the application
python app.py
```

The application will start at `http://localhost:5000` with pre-seeded demo spaces and personas!

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/spaces` | Query all active spaces with optional category filters |
| `GET` | `/api/spaces/<id>` | Retrieve detailed metadata, amenities, and AI specs for a space |
| `POST` | `/api/spaces/ai-scan` | Run AI Space Inspector on photos/notes to extract specs & price |
| `POST` | `/api/spaces` | Publish a new space listing |
| `POST` | `/api/spaces/ai-match` | Natural language seeker query matching & scoring |
| `POST` | `/api/bookings` | Instant booking + automated AI Micro-Lease generation |
| `POST` | `/api/calculator/estimate`| Dynamic pricing & host earnings calculation |
| `POST` | `/api/ai/chat` | Chat with LoopBot AI Concierge |

---

## 🏆 Hack2Ignite AI Disclosure

In accordance with Hack2Ignite guidelines:
- **LLM / AI Model Usage:** Used for multimodal space analysis, semantic matchmaking scoring, dynamic micro-leasing agreement synthesis, and real-time user assistance.
- **Architectural Fallback:** Includes deterministic heuristic algorithms ensuring zero disruption during live stage evaluations.
