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

## 🛠️ Tech Stack & Architecture

- **Backend:** Python 3, Flask 3.0, Flask-SQLAlchemy, SQLite / PostgreSQL, Flask-Login, Flask-WTF
- **Frontend:** React 18, Vite 5, Tailwind CSS, React Router 6, FontAwesome 6 (Permanent Dark Theme `#020617`)
- **AI Engine:** Multi-provider architecture supporting **Google Gemini** (`gemini-1.5-flash`) and **Groq** (`llama-3.3-70b-versatile`), backed by a deterministic conversational and heuristic fallback engine.
- **Zero-Hardware India Stack:**
  - **Section 52, Indian Easements Act, 1882:** Enforceable revocable micro-lease licenses (prevents adverse tenancy claims).
  - **DigiLocker & DPDP Act (2023):** SHA-256 masked Aadhaar OTP simulation (`XXXX-XXXX-4821`).
  - **Discom Electricity Meter Verification:** CA verification ensuring undisputed property dominion.
  - **UPI Escrow Protocol:** Automated ₹100 UPI security deposit held and instantly refunded upon check-out verification.
  - **GPS Geofence Handshake:** 50m radius virtual door access pass with fallback caretaker PIN.

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

# 4. (Optional) Set Environment Variables in .env
# Copy template from .env.example
cp .env.example .env

# 5. Provision Super Administrator (Optional CLI)
python scripts/create_admin.py --email admin@spaceloop.in --name "Platform Administrator"

# 6. Run the Flask Backend API (Port 5000)
python app.py

# 7. In a separate terminal, launch the React Frontend (Port 3000)
cd frontend
npm install
npm run dev
```

- **Frontend Web App:** `http://localhost:3000`
- **Backend API & Admin Portal:** `http://localhost:5000`

---

## 🔐 Authentication & Authorization Architecture

SpaceLoop employs an enterprise-grade, zero-trust authentication and access-control architecture:

### 1. Unified Identity & Decoupled Persona Contexts
- A user account maintains a single persistent identity while seamlessly toggling their active UI operational context (`host` vs. `seeker`) without mutating underlying credentials.
- Automatic context recovery via session state (`active_context`) with role-based dashboard filtering.

### 2. Authorization Matrix & Resource Ownership
- **Strict IDOR Protection:** Space owners cannot modify spaces owned by other hosts (`SPACE_UPDATE`). Seekers cannot check in, check out, or cancel bookings owned by other renters (`BOOKING_CHECKIN`, `BOOKING_CANCEL`).
- **Administrative Boundary:** Administrative privileges (`is_admin=True`) cannot be self-assigned through public registration. Administrators are provisioned via `scripts/create_admin.py` and have system-wide audit and moderation capabilities.

### 3. Security Controls & Defense-in-Depth
- **Password Hashing:** Werkzeug `scrypt`/`pbkdf2:sha256` with salt. Plaintext passwords are never stored or logged.
- **CSRF Protection:** Global `Flask-WTF` CSRF token verification across all state-changing HTML forms. REST API `/api/` and `/api/v1/` routes are exempt for programmatic and AJAX invocation.
- **Rate Limiting:** `Flask-Limiter` protects authentication endpoints (login: 5/min, registration: 3/min, password reset: 3/hour).
- **Session Protection:** Cookie hardening (`HttpOnly`, `SameSite=Lax`, `Session-Cookie` regeneration upon login).
- **Audit Logging:** Security events (`AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`, `AUTH_REGISTER_SUCCESS`, `AUTH_ADMIN_PROVISIONED`, `AUTH_LOGOUT`) are immutably recorded in the `audit_logs` database table.

---

## 👥 Pre-Seeded Test Fixtures & Demo Accounts

All seeded accounts have default password: **`password123`**

| Persona | Email | Role | Verification / Badges | Purpose |
|---|---|---|---|---|
| **Host (Delhi)** | `sunita@spaceloop.in` | Host (`owner`) | Discom Verified, UPI Penny Drop, OTI 99.2 | IIT Delhi study rooms host |
| **Seeker (Student)** | `aarav@iitd.ac.in` | Seeker (`seeker`) | DigiLocker Aadhaar, IIT Delhi `.ac.in` | Hackathon team lead renter |
| **Host (Dev)** | `dev-host@spaceloop.local` | Host (`owner`) | Discom Verified, UPI Verified | Automated test host fixture |
| **Seeker (Dev)** | `dev-seeker@spaceloop.local` | Seeker (`seeker`) | Student & Aadhaar Verified | Automated test seeker fixture |
| **Administrator** | `dev-admin@spaceloop.local` | Admin (`is_admin=True`) | Super Admin Authority | System governance & dispute admin |

---

## 📡 API Reference

### Core Business APIs
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/spaces` | Query all active spaces with optional category filters | Public |
| `GET` | `/api/spaces/<id>` | Retrieve detailed metadata, amenities, and AI specs | Public |
| `POST` | `/api/spaces/ai-scan` | Run AI Space Inspector on photos/notes to extract specs & price | Public |
| `POST` | `/api/spaces/ai-match` | Natural language seeker query matching & scoring | Public |
| `POST` | `/api/spaces` | Publish a new space listing | Host Only |
| `POST` | `/api/spaces/<id>/edit` | Edit space metadata and pricing (IDOR protected) | Space Owner |
| `POST` | `/api/spaces/<id>/toggle-status` | Pause / unpause space listing | Space Owner |
| `POST` | `/api/bookings` | Instant booking + automated AI Micro-Lease generation | Seeker Only |
| `POST` | `/api/booking/<id>/check-in` | GPS Geofence + QR code check-in handshake | Booking Renter |
| `POST` | `/api/booking/<id>/check-out`| Computer Vision room condition delta + ₹100 UPI refund | Booking Renter |
| `POST` | `/api/booking/<id>/cancel` | Cancel booking and release escrow deposit | Renter / Host |
| `POST` | `/api/calculator/estimate`| Dynamic pricing & host earnings calculation | Public |
| `POST` | `/api/ai/chat` | Chat with LoopBot AI Concierge | Public |
| `POST` | `/api/verify/student` | Verify student credentials via DigiLocker OTP & `.ac.in` | Public / Authed |
| `POST` | `/api/verify/host` | Verify host property via Discom CA bill & UPI penny drop | Public / Authed |

### Authentication & Identity APIs (v1)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate credentials & establish session |
| `POST` | `/api/v1/auth/register` | Register new seeker or host account |
| `POST` | `/api/v1/auth/logout` | Revoke session and clear cookies |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated user profile (safe sanitized) |

---

## 🧪 Automated Testing & Verification

Run the comprehensive automated security and functional test suites:

```bash
# 1. Run all 29 Unit, Authorization, IDOR, and Security Control Tests
python -m unittest discover tests

# 2. Run the 14-Point End-to-End Core Business Subsystem Functional Audit
python test_all_features_functional.py
```

---

## 🏆 Hack2Ignite AI Disclosure

In accordance with Hack2Ignite guidelines:
- **LLM / AI Model Usage:** Used for multimodal space analysis, semantic matchmaking scoring, dynamic micro-leasing agreement synthesis, and real-time user assistance.
- **Architectural Fallback:** Includes deterministic heuristic algorithms ensuring zero disruption during live stage evaluations.

