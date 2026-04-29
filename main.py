"""
FastAPI entry point for the Pregnancy Product Intelligence System.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import google_calendar
from crew import run_pipeline
from schemas import GoogleCalendarCreateRequest, PregnancyPlanOutput, PregnancyPlanRequest

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(
    title="Pregnancy Product Intelligence System",
    description=(
        "A CrewAI-powered planner for pregnancy week context, product intelligence, "
        "and stage-aware buying recommendations for Mumzworld."
    ),
    version="2.0.0",
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/pregnancy-plan", response_model=PregnancyPlanOutput)
async def generate_pregnancy_plan(request: PregnancyPlanRequest) -> PregnancyPlanOutput:
    return run_pipeline(
        due_date=request.due_date,
        mode=request.mode,
        include_debug=False,
    )


@app.get("/", include_in_schema=False)
async def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/privacy", include_in_schema=False)
async def privacy_policy():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""<!doctype html><html><head><title>Privacy Policy - DueDay Companion</title>
    <style>body{font-family:system-ui;max-width:700px;margin:40px auto;padding:0 20px;color:#333;line-height:1.7}</style></head><body>
    <h1>Privacy Policy</h1><p><strong>Last updated:</strong> April 2026</p>
    <p>DueDay Companion is a pregnancy planning tool. We respect your privacy.</p>
    <h2>Data We Collect</h2>
    <ul><li><strong>Due date</strong> you enter to generate your plan (not stored permanently)</li>
    <li><strong>Google Calendar access</strong> (only if you connect it) to add milestone reminders</li></ul>
    <h2>What We Don't Do</h2>
    <ul><li>We do not sell your data</li><li>We do not store personal health information</li>
    <li>We do not share data with third parties beyond Google Calendar (at your request)</li></ul>
    <h2>Google Calendar</h2>
    <p>If you connect Google Calendar, we only create milestone reminder events. We do not read, modify, or delete your existing events.</p>
    <h2>Contact</h2><p>For questions, open an issue at
    <a href="https://github.com/appu-ui/DueDay-Companion">github.com/appu-ui/DueDay-Companion</a></p>
    </body></html>""")


@app.get("/terms", include_in_schema=False)
async def terms_of_service():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""<!doctype html><html><head><title>Terms of Service - DueDay Companion</title>
    <style>body{font-family:system-ui;max-width:700px;margin:40px auto;padding:0 20px;color:#333;line-height:1.7}</style></head><body>
    <h1>Terms of Service</h1><p><strong>Last updated:</strong> April 2026</p>
    <h2>Acceptance</h2><p>By using DueDay Companion, you agree to these terms.</p>
    <h2>Service Description</h2><p>DueDay Companion provides AI-generated pregnancy product recommendations and milestone reminders.
    It is not a medical service and does not provide medical advice.</p>
    <h2>Disclaimer</h2>
    <ul><li>This tool is for <strong>informational purposes only</strong></li>
    <li>Always consult your doctor for medical decisions</li>
    <li>Product recommendations are suggestions, not prescriptions</li></ul>
    <h2>Limitation of Liability</h2>
    <p>DueDay Companion is provided "as is" without warranties. We are not liable for any decisions made based on the tool's output.</p>
    <h2>Contact</h2><p>For questions, open an issue at
    <a href="https://github.com/appu-ui/DueDay-Companion">github.com/appu-ui/DueDay-Companion</a></p>
    </body></html>""")


@app.get("/google-calendar/status")
def google_calendar_status() -> dict:
    return google_calendar.redact_status()


@app.get("/google-calendar/auth")
def google_calendar_auth() -> dict:
    try:
        return {"authorization_url": google_calendar.build_authorization_url()}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/google-calendar/callback", include_in_schema=False)
def google_calendar_callback(request: Request) -> RedirectResponse:
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(url=f"/?calendar_error={error}#calendar")
    if not request.query_params.get("code"):
        return RedirectResponse(url="/?calendar_error=missing_code#calendar")

    try:
        google_calendar.save_callback_credentials(str(request.url))
    except Exception as exc:
        return RedirectResponse(url=f"/?calendar_error={type(exc).__name__}#calendar")
    return RedirectResponse(url="/?calendar=connected#calendar")


@app.post("/google-calendar/events")
def create_google_calendar_events(payload: GoogleCalendarCreateRequest) -> dict:
    try:
        created = google_calendar.create_calendar_events(
            [event.model_dump() for event in payload.events]
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"created": created}


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "llm_configured": bool(os.getenv("GROQ_API_KEY")),
        "google_calendar_configured": google_calendar.is_configured(),
        "version": "2.0.0",
        "system": "pregnancy_product_intelligence",
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
