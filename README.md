# AutoSentinels 🚗🤖

AutoSentinels is an AI-powered vehicle health monitoring platform that helps drivers, OEMs, and fleet operators detect vehicle faults early, understand them clearly, and take proactive maintenance actions.

The system combines deterministic anomaly detection with LLM-powered explanations and chat, delivering reliability and clarity together.

---

## 🧩 Project Components

### 1️⃣ Driver App (Flutter)

A mobile-first interface for vehicle users.

**Features:**

- Enter Vehicle Identification Number (VIN)
- View active vehicle faults and severity
- AI chat assistant to ask questions like:
  - “What’s wrong with my car?”
  - “Is it safe to drive?”
- Chat history persists per VIN across app restarts

---

### 2️⃣ Backend (FastAPI)

The core intelligence and data layer.

**Responsibilities:**

- Telemetry ingestion endpoint
- Rule-based anomaly detection (deterministic & stable)
- Fault storage and retrieval
- LLM-powered explanations and summaries
- Chat API for driver and OEM assistants

**Key Design Choice:**

- Rule-based engine decides what failed
- LLM explains why and what to do next

---

### 3️⃣ OEM / Fleet Console (Streamlit)

An operational dashboard for OEMs and fleet managers.

**Planned Features:**

- Fleet health dashboard (KPIs & charts)
- Vehicle list with fault status
- Fault browser with filters
- Vehicle detail pages with AI summaries
- OEM AI assistant for fleet-level questions
- Optional telemetry simulator for live demos

---

## 🔁 End-to-End Flow

1. Vehicle sends telemetry data (temperature, voltage, vibration, etc.)
2. Backend analyzes data using rule-based anomaly detection
3. Faults are created with severity and predicted failure distance
4. LLM generates human-readable explanations
5. Driver app and OEM console display insights
6. Users can chat with an AI assistant for clarity

---

## 🛠️ Tech Stack

- Frontend (Driver App): Flutter, Provider, SharedPreferences
- OEM Console: Streamlit (Python)
- Backend: FastAPI (Python)
- AI / LLM: Claude or GPT via LangChain
- Storage: Lightweight persistence (demo-focused)

---

## ✨ Key Highlights

- Deterministic fault detection (no hallucinations)
- LLM-powered explanations and chat
- Persistent chat history per VIN
- Clear separation of concerns (detection vs explanation)
- Demo-ready, production-inspired architecture`

---

## 🧠 Future Enhancements

- Predictive maintenance scheduling
- Fleet risk scoring
- Maintenance ticket generation
- Real-time telemetry streaming
- User-reported symptom integration

---

## 📌 Summary

AutoSentinels turns raw vehicle telemetry into actionable insights and friendly explanations for both drivers and fleet operators.
