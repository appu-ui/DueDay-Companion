"""
Google Calendar OAuth and event creation helpers.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "google_calendar_token.json"
CLIENT_SECRET_PATH = Path(os.getenv("GOOGLE_CLIENT_SECRET_FILE", BASE_DIR / "credentials.json"))
SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://127.0.0.1:8000/google-calendar/callback")
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def is_configured() -> bool:
    return CLIENT_SECRET_PATH.exists()


def get_credentials() -> Credentials | None:
    if not TOKEN_PATH.exists():
        return None

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds if creds and creds.valid else None


def is_connected() -> bool:
    return get_credentials() is not None


def build_authorization_url(redirect_uri: str = None) -> str:
    if not is_configured():
        raise FileNotFoundError(f"Missing Google OAuth client secret file: {CLIENT_SECRET_PATH}")

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=redirect_uri or REDIRECT_URI,
    )
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url


def save_callback_credentials(callback_url: str, redirect_uri: str = None) -> None:
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=redirect_uri or REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=callback_url)
    TOKEN_PATH.write_text(flow.credentials.to_json(), encoding="utf-8")


def _event_body(event: dict[str, Any]) -> dict[str, Any]:
    start_date = date.fromisoformat(event["date"])
    end_date = start_date + timedelta(days=1)
    return {
        "summary": event["title"],
        "description": event["description"],
        "start": {"date": start_date.isoformat()},
        "end": {"date": end_date.isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},
                {"method": "email", "minutes": 24 * 60},
            ],
        },
    }


def create_calendar_events(events: list[dict[str, Any]], calendar_id: str = "primary") -> list[dict[str, Any]]:
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google Calendar is not connected.")

    service = build("calendar", "v3", credentials=creds)
    created = []
    for event in events:
        inserted = service.events().insert(
            calendarId=calendar_id,
            body=_event_body(event),
            sendUpdates="none",
        ).execute()
        created.append(
            {
                "id": inserted.get("id"),
                "htmlLink": inserted.get("htmlLink"),
                "summary": inserted.get("summary"),
                "date": event["date"],
            }
        )
    return created


def redact_status() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "connected": is_connected(),
        "client_secret_path": str(CLIENT_SECRET_PATH),
        "token_saved": TOKEN_PATH.exists(),
    }
