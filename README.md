# DueDay Companion 🤰🛍️

A multi-agent AI system powered by CrewAI and LLaMA 3.3 that analyzes pregnancy timelines to output structured, safe, bilingual (English + Arabic) insights along with relevant, stage-aware product recommendations for Mumzworld.

🔗 **Live Demo**: [https://dueday-companion.onrender.com](https://dueday-companion.onrender.com)

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
GEMINI_API_KEY=your_gemini_key_here
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
