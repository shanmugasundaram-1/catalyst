# 🌸 AyuCare — Elderly Care & Medication Management Platform
> **Built for PromptWars x Catalyst 2026 (Google Build with AI Hackathon)**
> *Keeping the elderly person at the center of their own healthcare decisions.*

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🌟 Problem Statement Alignment

**Problem**: Elderly patients often miss medications, have no structured handoff between elder → caretaker → family, and face language and literacy barriers — especially in multilingual households.

**AyuCare solves this with:**
| Challenge | AyuCare Solution |
|---|---|
| Medication forgetting | Giant one-tap "I Took It" button + APScheduler escalation chain |
| Elder disempowerment | Elder must approve every caretaker/family proposal |
| Language barriers | Full trilingual UI + voice assistant (English, தமிழ், हिन्दी) |
| Missed-dose blind spots | AI Early Warning with 14-day pattern analysis via Gemini |
| Communication gaps | Per-language email alerts for each family member's preferred language |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, FastAPI 0.115, SQLAlchemy 2.0 (MySQL + SQLite fallback), Pydantic v2, PyJWT + bcrypt, APScheduler 3.x |
| **Frontend** | React 19, Vite 8, Tailwind CSS v4, Lucide Icons, Recharts, react-i18next |
| **AI** | Google Gemini API (`google-genai` SDK) — `gemini-2.5-flash` for voice NLU, prescription scanning, drug interaction checks, weekly summaries, and care insights |
| **Email** | SMTP (Gmail App Password) + in-memory Live Email Inspector for demo |
| **Languages** | English (`en`) · Tamil / தமிழ் (`ta`) · Hindi / हिन्दी (`hi`) |

---

## ✨ Core Features

### 🏥 Elder-First Architecture
- **Passcode-Based Shared Access**: Three separate passcodes (`ELDER`, `CARETAKER`, `FAMILY`) on one profile
- **Elder Approval Workflow**: Caretaker/family proposals remain `PENDING` until the elder confirms — reversing the usual caretaker-centric model
- **High-contrast, large-typography UI** with `Noto Sans Devanagari` and Tamil font support

### 🎙️ Feature A — Multilingual Voice Assistant
- **Large floating mic button** on the Today screen with animated Listening → Processing → Speaking states
- **Web Speech API** (`en-IN`, `ta-IN`, `hi-IN`) for speech-to-text + `speechSynthesis` for spoken replies
- **POST `/api/voice/intent`**: Gemini 2.5 Flash classifies intent (`MARK_DOSE_TAKEN`, `NEXT_DOSE_QUERY`, `APPOINTMENT_QUERY`, `SOS`, `UNKNOWN`) in English, Tamil, Hindi, Tanglish, and Hinglish
- **Fuzzy medicine matching** by spoken name or condition alias (BP → Telmisartan/Amlodipine, Sugar → Metformin/Glimepiride)
- **SOS safety gate**: voice/tap confirmation required before dispatching emergency emails
- **Graceful fallback**: if Gemini fails, rule-based multilingual regex kicks in; if speech API unavailable, text input is shown instead

### 🔮 Feature B — AI Early Warning & Care Insights
- **14-day dose log analysis** (APScheduler daily job) detecting:
  - Repeated misses at the same time slot (≥ 3 occurrences)
  - Adherence drop > 20% vs previous week (escalates to `urgent` if drop > 35%)
  - Medicine stock expiring within 3 days
  - Upcoming appointments within 48 h
- **Gemini-generated** warm, plain-language insight text in EN + TA + HI per insight
- **48-hour duplicate suppression** — same insight type not re-sent within 48 h per elder
- **Colour-coded dashboard card** (🔴 urgent / 🟡 warning / 🔵 info)
- **Template fallback** — if Gemini is unavailable, deterministic trilingual templates ensure alerts still fire

### 🤖 Gemini AI Suite
1. **Prescription Scanner** — multimodal vision extracts medicine name, dosage, schedule from photos
2. **Natural-Language Entry** — converts free-text to structured schedule (`"Metformin 500mg morning after food for 30 days"`)
3. **Drug & Food Interaction Check** — severity-rated warnings with medical disclaimers
4. **Weekly Family Care Digest** — empathetic weekly summaries in each family member's language

### 📧 Smart Email Escalation Chain (APScheduler)
| Trigger | Recipient | Language |
|---|---|---|
| 10 min before dose | Elder | Elder's language |
| 15 min past due | Elder | Elder's language |
| 30 min past due | Caretaker | Caretaker's language |
| 45 min past due | Family | Family's language |
| 24 h & 2 h before appointment | Elder + Caretaker | Per-user language |

---

## 🔐 Security

- **Credentials in `.env` only** — no secrets in source code; `.env` is gitignored
- **bcrypt** password hashing with per-user salts
- **JWT** access tokens with configurable expiry
- **CORS** restricted to explicit origins in production (`APP_ENV != development`)
- **Role-based access enforcement** at every endpoint (FAMILY = read-only, ELDER approval required for mutations)
- **Input validation** via Pydantic v2 schemas on all request bodies
- `.env.example` contains only placeholder values — safe to commit

---

## ♿ Accessibility

- **WCAG-aware** high-contrast color palette (emerald/slate with 4.5:1+ contrast ratios)
- **Large touch targets** (≥ 48 × 48 px) on elder-facing buttons
- Semantic HTML with `aria-label` on icon-only buttons
- `lang` attribute mapped to active i18n language for screen readers
- Font stack: `Noto Sans` (Latin), `Noto Sans Devanagari` (Hindi), system Tamil fonts
- Voice assistant falls back gracefully when Speech API is unsupported (no crash, text input shown)

---

## ⚡ Efficiency

- **SQLAlchemy connection pooling** with MySQL (pool_recycle to handle wait_timeout)
- **APScheduler** runs at minute-level granularity — only fires when due doses exist
- **48-hour duplicate suppression** on insights prevents email floods
- **React**: lazy-loaded modals; Vite HMR + tree-shaking for fast builds
- **Gemini API calls** are async-safe and wrapped in try/except with rule-based fallbacks — zero crash on API quota

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+ · Node.js 18+ · MySQL 8.0 (or use SQLite — zero config!)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) *(optional — works with mock fallback)*

### 2. Backend Setup

```powershell
# Clone & navigate
cd catalyst

# Activate Python virtual environment
.\venv\Scripts\Activate.ps1          # Windows PowerShell
# source venv/bin/activate           # macOS / Linux

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — add GEMINI_API_KEY and SMTP credentials (or leave SMTP_MOCK=true)
```

**MySQL Setup** (skip if using SQLite):
```sql
CREATE DATABASE ayucare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Then set `DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ayucare?charset=utf8mb4` in `backend/.env`.

**SQLite (zero-config demo)**:
Set `DATABASE_URL=sqlite:///./ayucare.db` in `backend/.env`.

### 3. Seed & Test

```powershell
$env:PYTHONPATH="backend"

# Seed demo data (creates elder + caretaker + family + medications + 14-day dose history + insights)
python backend/seed_data.py

# Run test suite (17 tests covering auth, roles, voice NLU, insights deduplication, email language)
python -m pytest backend/tests/ -v
```

### 4. Start Backend

```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
→ **API docs**: http://localhost:8000/docs
→ **Health check**: http://localhost:8000/api/health

### 5. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```
→ Open: **http://localhost:5173**

---

## 🔑 Pre-Seeded Demo Logins (1-Click on Login Screen)

| Role | Profile ID | Passcode | Name | Language | Capabilities |
|---|---|---|---|---|---|
| 👴 **Elder** | `DEMO-ELDER` | **`1111`** | Broly | **Tamil (ta)** | Full control · approves changes · SOS · voice assistant |
| 🩺 **Caretaker** | `DEMO-ELDER` | **`2222`** | Priya (Nurse) | **English (en)** | Manages meds & appointments (proposals need elder approval) |
| 👨‍👩‍👧 **Family** | `DEMO-ELDER` | **`3333`** | Karthik (Son) | **Hindi (hi)** | Observer · receives Hindi alerts & summaries |

---

## 🧪 Feature Verification Guide

### ① Elder-First Today Screen
- Log in as **Elder (1111)** → see the giant **"YOUR NEXT MEDICINE"** card
- Tap **"YES, I TOOK THIS MEDICINE"** → dose marked TAKEN, stock decrements, next dose shown

### ② Caretaker Proposal → Elder Approval Workflow
- Switch to **Caretaker (2222)** → Medications → **"+ Add Medicine"**
- Returns: *"Proposal submitted! Awaiting Elder confirmation"*
- Switch to **Elder (1111)** → **Pending Approvals** → Approve → medicine added instantly

### ③ 🎙️ Voice Assistant (Feature A)
- Log in as **Elder (1111)** → Today screen → tap the green **"Tap to speak a command"** button
- Try Tamil: *"BP maathirai saapten"* → Gemini detects MARK_DOSE_TAKEN intent, marks dose, replies in Tamil
- Try Hindi: *"अगली दवा कब है?"* → replies with next dose time in Hindi
- Try English: *"Do I have an appointment tomorrow?"* → queries DB and speaks reply
- SOS: say *"Emergency"* → asks for confirmation → tap **"Yes, Send Emergency SOS"** → emails dispatched
- Check **📧 Emails** button → Live Email Inspector shows SOS emails in caretaker's English & family's Hindi

### ④ 🔮 AI Early Warning & Care Insights (Feature B)
- Today screen → scroll to **"AI Early Warning & Care Insights"** card
- Seed data creates missed evening doses for 4+ days → insight auto-generated on startup
- Colour-coded cards: 🔴 Urgent / 🟡 Warning / 🔵 Info
- Tap **"Run 14-Day AI Scan Now"** to trigger on-demand analysis
- Tap **"Acknowledge"** on any insight to mark as seen
- Check Live Email Inspector for per-language insight emails (EN for caretaker, HI for family)

### ⑤ Gemini AI Tools
- Today screen → **"✨ Scan Prescription"** → upload prescription image or enter natural text
- **"🛡️ Safety & Food Check"** → type *"Aspirin"* against active BP + diabetes medicines
- **"📋 Weekly Summary"** → generates empathetic report for family in their language

### ⑥ Adherence Analytics
- **"Health Adherence"** tab → Recharts interactive charts for 7/14/30-day trends, streak counters

### ⑦ Multilingual Switching
- Language selector (top-right) → switch between 🇬🇧 English / 🇮🇳 தமிழ் / 🇮🇳 हिन्दी
- **All UI strings, email templates, voice replies, and AI-generated insights** switch with the user's saved language

---

## 📁 Repository Structure

```
catalyst/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app · lifespan · CORS · routers
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings (all secrets from .env)
│   │   │   ├── database.py            # SQLAlchemy engine + schema migration helper
│   │   │   ├── security.py            # bcrypt hashing · JWT create/decode
│   │   │   └── dependencies.py        # Auth dependency · activity log helper
│   │   ├── models/
│   │   │   └── __init__.py            # SQLAlchemy ORM: Profile, Medication, DoseLog,
│   │   │                              #   Appointment, PendingChange, ActivityLog, CareInsight
│   │   ├── schemas/
│   │   │   └── __init__.py            # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── voice_service.py       # [Feature A] Voice NLU · Gemini intent classification
│   │   │   ├── insights_service.py    # [Feature B] 14-day analysis · Gemini insight writer
│   │   │   ├── gemini_service.py      # Prescription scan · drug check · weekly summary
│   │   │   ├── email_service.py       # Trilingual HTML email templates · SMTP/mock sender
│   │   │   ├── dose_service.py        # Dose scheduling, next-dose query, adherence calc
│   │   │   └── scheduler_service.py   # APScheduler: escalation chain + daily insights job
│   │   └── routers/
│   │       ├── auth.py                # POST /api/auth/join  GET /api/auth/me
│   │       ├── profiles.py            # Profile management · language update
│   │       ├── medications.py         # CRUD medications with elder-approval flow
│   │       ├── doses.py               # Dose actions · today overview · adherence
│   │       ├── appointments.py        # Appointment CRUD with approval flow
│   │       ├── approvals.py           # Elder approve/reject pending changes
│   │       ├── activity.py            # Care activity feed
│   │       ├── ai.py                  # Gemini AI endpoints (scan, NL entry, safety, summary)
│   │       ├── sos.py                 # Emergency SOS broadcast
│   │       ├── voice.py               # [Feature A] POST /api/voice/intent
│   │       └── insights.py            # [Feature B] GET/POST /api/insights
│   ├── tests/
│   │   ├── test_auth_roles.py         # Auth · roles · approval workflow (8 tests)
│   │   ├── test_ai_and_notifications.py  # Gemini NLP · email escalation (5 tests)
│   │   └── test_multilingual.py       # Voice NLU · insights deduplication · language (8 tests)
│   ├── seed_data.py                   # Demo seeder: elder + caretaker + family + 14-day history
│   ├── requirements.txt               # Pinned Python dependencies
│   └── .env.example                   # Template (placeholder values only — safe to commit)
├── frontend/
│   ├── src/
│   │   ├── api/client.js              # Typed REST API client
│   │   ├── context/AuthContext.jsx    # Auth state · quick role switcher
│   │   ├── components/
│   │   │   ├── VoiceAssistantModal.jsx  # [Feature A] Mic UI · speech API · spoken replies
│   │   │   ├── CareInsightsCard.jsx     # [Feature B] Insights dashboard card
│   │   │   ├── Navbar.jsx               # Responsive nav · language picker · email inspector toggle
│   │   │   ├── ElderDoseCard.jsx        # Giant elder-focused next-dose card
│   │   │   ├── SOSModal.jsx             # Emergency SOS confirmation modal
│   │   │   ├── AIModal.jsx              # Prescription scanner + NL entry
│   │   │   ├── InteractionCheckerModal.jsx  # Drug/food safety check
│   │   │   ├── WeeklySummaryModal.jsx   # AI weekly family digest
│   │   │   └── LiveEmailDrawer.jsx      # In-memory email audit inspector
│   │   ├── pages/
│   │   │   ├── TodayPage.jsx            # Elder Today hub (voice button + insights + dose card)
│   │   │   ├── MedicationsPage.jsx
│   │   │   ├── ApprovalsPage.jsx
│   │   │   ├── AppointmentsPage.jsx
│   │   │   ├── AdherencePage.jsx        # Recharts adherence visualizations
│   │   │   ├── ActivityPage.jsx
│   │   │   └── LoginPage.jsx            # 1-click demo login buttons
│   │   ├── i18n/
│   │   │   ├── en.json                  # English strings
│   │   │   ├── ta.json                  # Tamil strings (தமிழ்)
│   │   │   ├── hi.json                  # Hindi strings (हिन्दी)
│   │   │   └── index.js                 # i18next config
│   │   ├── App.jsx                      # Root layout · modal orchestration
│   │   └── index.css                    # Tailwind CSS v4 · Tamil/Devanagari font imports
│   ├── package.json
│   └── vite.config.js
├── .gitignore                           # Excludes .env, node_modules, *.db, __pycache__, etc.
└── README.md
```

---

## 🧪 Running Tests

```powershell
$env:PYTHONPATH="backend"

# All tests with verbose output
python -m pytest backend/tests/ -v

# Run only voice/insights/multilingual tests
python -m pytest backend/tests/test_multilingual.py -v

# Run with coverage report
python -m pytest backend/tests/ --tb=short -q
```

**Test coverage areas:**
| Module | Tests |
|---|---|
| Auth & Role enforcement | 8 tests |
| Gemini NLP + email escalation | 5 tests |
| Voice intent (EN/TA/HI) + dose update | 4 tests |
| Insights deduplication + email language | 3 tests |
| Language persistence + mark-seen | 3 tests |

---

## 🛡️ License

MIT License · Developed for PromptWars x Catalyst 2026 · Google Build with AI Hackathon
