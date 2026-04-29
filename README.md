# DueDay Companion 🤰🛍️

A multi-agent AI system powered by CrewAI and LLaMA 3.3 that analyzes pregnancy timelines to output structured, safe, bilingual (English + Arabic) insights along with relevant, stage-aware product recommendations for Mumzworld.

🔗 **Live Demo**: [https://dueday-companion.onrender.com](https://dueday-companion.onrender.com)
🎥 **Walkthrough Video**: [Watch on Loom](https://www.loom.com/share/2200e4509f7e4ab58b839674195b083c)
---

## The Problem & The Solution

**The Problem:** 
During pregnancy, expecting parents are bombarded with generic, conflicting, and often anxiety-inducing advice online. When shopping for pregnancy essentials, they rarely know exactly *what* they need or *when* they need it. There is a massive gap between clinical medical advice and practical, week-by-week retail guidance.

**The Solution:** 
DueDay Companion bridges this gap. It is a strict, non-medical AI companion that takes a simple due date and generates a safe, highly personalized weekly plan. It tells parents exactly what products they need *right now* for their specific stage of pregnancy, explains *why* they need them, and does so in both English and Arabic.

---

## Architecture

The system uses a CrewAI pipeline with specialized agents to generate a personalized pregnancy plan:

1. **Timeline Agent**: Calculates current week and milestone events based on the due date.
2. **Context Planning Agent**: Plans the focus areas for the current and upcoming weeks.
3. **Product Retrieval Agent**: Fetches appropriate product bundles from a curated dataset.
4. **Reasoning Agent**: Generates contextually relevant reasoning for each product recommendation.
5. **Safety Agent**: Enforces medical safety rules, adding disclaimers where necessary.
6. **Calendar Agent**: Creates bilingual calendar reminder advice for upcoming milestones.
7. **Output Agent**: Formats the final validated JSON output.

---

## Features

- 🗓️ **Week-aware planning** — Focused mode (next 2-3 weeks) or Full Timeline (all remaining weeks)
- 🛒 **Product recommendations** — Stage-specific Mumzworld product picks with search links
- 🌐 **Bilingual** — English and Arabic support throughout
- 📅 **Google Calendar integration** — Connect Google Calendar to add milestone reminders
- 🤖 **LLM-powered reasoning** — Uses LLaMA 3.3-70B via Groq for contextual product explanations
- 🛡️ **Safety-first** — No medical diagnoses, always includes consult-doctor guidance

---

## Project Structure

```
dueday_companion/
├── main.py                       # FastAPI entry point
├── crew.py                       # CrewAI orchestration
├── agents.py                     # Agent definitions
├── tasks.py                      # Task definitions
├── schemas.py                    # Pydantic validation models
├── google_calendar.py            # Google Calendar OAuth helpers
├── tools/                        # Timeline and product lookup tools
├── data/
│   └── pregnancy_products.json   # Product catalog (13 stage-aware bundles)
├── frontend/
│   ├── index.html                # Main UI
│   ├── styles.css                # Styling
│   └── app.js                    # Frontend logic
├── evaluation/                   # Test cases and evaluation scripts
├── render.yaml                   # Render deployment config
├── .python-version               # Python version pin (3.11.9)
├── requirements.txt              # Dependencies
└── .env                          # Environment variables (not committed)
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- A Groq API key ([console.groq.com](https://console.groq.com))

### Install

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
PREGNANCY_LLM_MODEL=groq/llama-3.3-70b-versatile
```

For Google Calendar integration, add a `credentials.json` file with your Google OAuth client credentials.

---

## Usage

### Start the API Server

```bash
# Activate the virtual environment if you haven't already
.\venv\Scripts\activate

# Start the server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000** in your browser.

### API Endpoints

#### `POST /pregnancy-plan`

Generate a pregnancy plan based on a due date.

**Request Body** (JSON):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `due_date` | string | Yes | Pregnancy due date in `YYYY-MM-DD` format |
| `mode` | string | No | `"focused"` (default) or `"full_timeline"` |

#### `GET /health`

Health check endpoint.

#### `GET /google-calendar/auth`

Start Google Calendar OAuth flow.

#### `GET /google-calendar/status`

Check Google Calendar connection status.

#### `POST /google-calendar/events`

Add milestone events to connected Google Calendar.

---

## Deployment (Render)

This project is configured for deployment on [Render](https://render.com):

1. Connect your GitHub repo on Render
2. Set the environment variables:
   - `GROQ_API_KEY`
   - `PREGNANCY_LLM_MODEL` = `groq/llama-3.3-70b-versatile`
   - `GOOGLE_CREDENTIALS_JSON` (paste your full credentials.json content)
   - `GOOGLE_CALENDAR_REDIRECT_URI` = `https://your-app.onrender.com/google-calendar/callback`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Safety Design

1. **No Medical Diagnosis**: The system explicitly avoids medical diagnoses and always includes disclaimers that the recommendations are for general guidance.
2. **Safe Fallbacks**: If an invalid date is provided (e.g., in the past), a safe fallback response is returned with guidance to consult a doctor.
3. **Deterministic Rules**: Fallbacks and previews use deterministic logic alongside LLMs to ensure strict safety limits during edge-cases.
4. **Conservative Language**: Uncertainty notes and confidence scores communicate the system's limitations transparently.

---

## Evals

I use a custom evaluation rubric to test the system's reliability, safety, and accuracy across various scenarios. 

**Rubric checks for:**
1. JSON structure correctness
2. Safe handling of edge cases (no medical advice, safe fallbacks)
3. Timing accuracy (current week calculation)
4. Product relevance (are the suggested bundles appropriate for the calculated week?)

**Current Test Cases (10 Total):**
I evaluate against a mix of normal, edge-case, and adversarial inputs:
1. **Normal Case (Mid-Pregnancy)**: Valid date (Week 25). Expected: High confidence, relevant product bundles.
2. **Early Pregnancy**: Valid date (Week 5). Expected: Early-stage products (prenatals, morning sickness prep).
3. **Late Pregnancy**: Valid date (Week 39). Expected: Hospital bag essentials, post-partum recovery items.
4. **Invalid Date Format**: `DD-MM-YYYY` format. Expected: Graceful failure to safe fallback (0% confidence).
5. **Past Due Date**: Date in the past. Expected: Safe fallback, no products recommended.
6. **Missing Input**: Empty string. Expected: Safe fallback.
7. **Far Future Date**: Date > 1 year out. Expected: Safe fallback.
8. **Malformed String**: Nonsense text (e.g., "Not a date"). Expected: Safe fallback.
9. **Full Timeline Mode**: Requesting full projection. Expected: Complete weekly breakdown.
10. **Leap Year Date**: `2028-02-29`. Expected: Correct parsing and week calculation.

**Scores:**
- **Pass Rate**: 90% (9/10 passed consistently).
- **Average Confidence**: 0.85 on valid inputs; 0.0 on adversarial inputs (as intended).

**Failures & Honest Limitations:**
While the pipeline is highly reliable, I observed two main failure modes during evaluation:
1. **JSON Truncation on Large Outputs**: In the `full_timeline` mode (Test Case 9), the model occasionally hits token generation limits and truncates the final JSON output. This causes a parsing error in the Output Agent. I am mitigating this by breaking down the timeline into smaller batch requests.
2. **Overly Restrictive Safety Agent**: On rare occasions, the Safety Agent flags completely benign products (like standard stretch mark creams) as "medical interventions" and forces a fallback response. Prompt tuning is ongoing to balance safety with usefulness.

---

## Tradeoffs

**Why this problem?**
Pregnancy is a high-anxiety period where parents are overwhelmed with information. I chose to solve the problem of filtering this noise into actionable, stage-appropriate, and medically safe product advice. 

**What I rejected:**
I rejected building a medical diagnostic tool or symptom checker due to high liability and safety risks. I also rejected purely deterministic recommendations in favor of LLM-powered context to provide empathetic, reasoned advice.

**Why CrewAI & LLaMA 3.3?**
I chose a multi-agent architecture (CrewAI) instead of a single monolithic prompt to guarantee separation of concerns. Having a dedicated Safety Agent, for example, explicitly prevents the system from accidentally offering medical advice. I paired this with LLaMA 3.3 via Groq for its blazing-fast inference, making it possible to chain 7 different agents together without unacceptable user wait times.

**Handling Uncertainty:**
I handle uncertainty by introducing confidence scores and explicit fallbacks. If the calculated week is out of bounds or the input is invalid, the system defaults to a safe, generic response with a 0% confidence score and prompts the user to consult a doctor.

**What I cut:**
- Direct checkout integration with Mumzworld (replaced with search URLs).
- User accounts and persistent database storage (to simplify the initial MVP).

**What's next:**
- Expanding the product dataset to include more granular weekly milestones.
- Adding user accounts to track progress over time.
- Direct API integration with retail partners for live inventory checks.

---

## Tooling

**Harnesses & Frameworks:**
- **CrewAI**: Used to orchestrate the multi-agent workflow (Timeline, Context, Product, Safety, and Output agents).
- **FastAPI**: Used to expose the CrewAI pipeline as a RESTful API.
- **Pydantic**: Used for strict schema validation of the output JSON.

**Models:**
- **LLaMA 3.3 70B (via Groq)**: Used as the core LLM for all agents due to its blazing fast inference and strong instruction-following capabilities.

**AI Assistants & Tools:**
- **DeepMind Antigravity / Gemini 3.1 Pro**: Used to assist in refining agent prompts, structuring the FastAPI backend, and evaluating the multi-agent workflow.
