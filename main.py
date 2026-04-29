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
        "llm_configured": bool(os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")),
        "google_calendar_configured": google_calendar.is_configured(),
        "version": "2.0.0",
        "system": "pregnancy_product_intelligence",
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
