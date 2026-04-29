"""
Deterministic pregnancy timeline and planning tools.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from crewai.tools import tool

MAX_REASONABLE_DUE_DAYS = 320
PREGNANCY_LENGTH_DAYS = 280
MILESTONE_WEEKS = [12, 20, 28, 32, 36, 40]


def calculate_pregnancy_timeline(due_date_text: str) -> dict:
    if not due_date_text or not str(due_date_text).strip():
        return {
            "ok": False,
            "error": "missing_due_date",
            "message": "Due date is required.",
        }

    try:
        due_date = datetime.strptime(str(due_date_text).strip(), "%Y-%m-%d").date()
    except ValueError:
        return {
            "ok": False,
            "error": "invalid_due_date",
            "message": "Due date must be in YYYY-MM-DD format.",
        }

    today = date.today()
    days_until_due = (due_date - today).days
    if days_until_due < 0:
        return {
            "ok": False,
            "error": "past_due_date",
            "message": "Due date is in the past.",
            "days_until_due": days_until_due,
        }

    if days_until_due > MAX_REASONABLE_DUE_DAYS:
        return {
            "ok": False,
            "error": "far_future_due_date",
            "message": "Due date is unusually far in the future. Please confirm it.",
            "days_until_due": days_until_due,
        }

    pregnancy_start = due_date - timedelta(days=PREGNANCY_LENGTH_DAYS)
    gestation_days = (today - pregnancy_start).days
    current_week = max(1, min(40, gestation_days // 7 + 1))

    trimester = 1 if current_week <= 13 else 2 if current_week <= 27 else 3
    return {
        "ok": True,
        "due_date": due_date.isoformat(),
        "today": today.isoformat(),
        "current_week": current_week,
        "trimester": trimester,
        "days_until_due": days_until_due,
    }


def build_context_plan(current_week: int, mode: str = "focused") -> dict:
    normalized_mode = (mode or "focused").strip().lower()
    preview_weeks = list(range(current_week + 1, min(40, current_week + 3) + 1))

    upcoming_milestones = [week for week in MILESTONE_WEEKS if week >= current_week][:3]
    if current_week not in upcoming_milestones and current_week in MILESTONE_WEEKS:
        upcoming_milestones.insert(0, current_week)
    upcoming_milestones = upcoming_milestones[:3]

    plan = {
        "mode": normalized_mode,
        "current_week": current_week,
        "preview_weeks": preview_weeks,
        "milestone_weeks": upcoming_milestones,
        "selected_weeks": [current_week] + preview_weeks,
    }

    if normalized_mode == "full_timeline":
        plan["full_timeline_weeks"] = list(range(current_week, 41))

    return plan


@tool("Pregnancy Timeline Tool")
def timeline_tool(due_date_text: str) -> str:
    """Calculate the current pregnancy week from a due date."""
    return json.dumps(calculate_pregnancy_timeline(due_date_text), ensure_ascii=False)


@tool("Context Planning Tool")
def context_planning_tool(current_week: int, mode: str = "focused") -> str:
    """Select the current week, next 2-3 weeks, and milestone weeks."""
    return json.dumps(build_context_plan(int(current_week), mode), ensure_ascii=False)
