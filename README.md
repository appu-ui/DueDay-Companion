# Pregnancy Product Intelligence System 🤰🛍️

A multi-agent AI system powered by CrewAI that analyzes pregnancy timelines to output structured, safe, bilingual (English + Arabic) insights along with relevant, stage-aware product recommendations for Mumzworld.

---

## Architecture

The system uses a CrewAI pipeline with specialized agents to generate a personalized pregnancy plan:

1. **Timeline Agent**: Calculates current week and milestone events based on the due date.
2. **Context Planning Agent**: Plans the focus areas for the current and upcoming weeks.
3. **Product Retrieval Agent**: Fetches appropriate product bundles from a curated dataset.
4. **Reasoning Agent**: Generates contextually relevant reasoning for each product recommendation.
5. **Safety Agent**: Enforces medical safety rules, adding disclaimers where necessary.
6. **Output Agent**: Formats the final validated JSON output.

---

## Project Structure

```
dueday_companion/ (Directory Name)
├── main.py                       # FastAPI entry point
├── crew.py                       # CrewAI orchestration
├── agents.py                     # Agent definitions
├── tasks.py                      # Task definitions
├── schemas.py                    # Pydantic validation models
├── tools/                        # Timeline and product lookup tools
├── .env                          # Environment variables
└── requirements.txt
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- A Google Gemini API key

### Install

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure

Ensure you have a `.env` file in the project root with your Gemini key:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

### Start the API Server

```bash
# Activate the virtual environment if you haven't already
.\venv\Scripts\activate

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*(Note: if port 8000 is occupied, you can change the port using `--port 8001`)*

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

---

## Quick Testing / Example

If you want to test the API but don't know what input to provide, you can simulate being midway through pregnancy by using a due date about 4-5 months in the future. 

**Using cURL (Command Prompt / Bash):**
```bash
curl -X POST http://localhost:8001/pregnancy-plan \
  -H "Content-Type: application/json" \
  -d "{\"due_date\": \"2026-10-15\", \"mode\": \"focused\"}"
```

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/pregnancy-plan" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"due_date": "2026-10-15", "mode": "focused"}'
```

*(Note: Adjust the port to 8000 if your server is running on the default port)*

---

## Safety Design

1. **No Medical Diagnosis**: The system explicitly avoids medical diagnoses and always includes disclaimers that the recommendations are for general guidance.
2. **Safe Fallbacks**: If an invalid date is provided (e.g., in the past), a safe fallback response is returned with guidance to consult a doctor.
3. **Deterministic Rules**: Fallbacks and previews use deterministic logic alongside LLMs to ensure strict safety limits during edge-cases.
