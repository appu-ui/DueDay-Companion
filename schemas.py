"""
Pydantic schemas for the Pregnancy Product Intelligence System.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


VALID_MODES = {"focused", "full_timeline"}


class PregnancyPlanRequest(BaseModel):
    due_date: Optional[str] = Field(default=None, description="Pregnancy due date in YYYY-MM-DD format")
    mode: str = Field(default="focused", description="focused or full_timeline")

    @field_validator("mode")
    @classmethod
    def mode_must_be_valid(cls, value: str) -> str:
        normalized = (value or "focused").strip().lower()
        if normalized not in VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
        return normalized


class ProductReason(BaseModel):
    en: str
    ar: str


class ProductItem(BaseModel):
    name: str
    url: str
    reason: ProductReason
    timing: str


class PreviewItem(BaseModel):
    week: int = Field(..., ge=1, le=40)
    focus: str
    buy: List[str] = Field(default_factory=list)


class MilestoneItem(BaseModel):
    week: int = Field(..., ge=1, le=40)
    event: str


class CalendarEventItem(BaseModel):
    week: int = Field(..., ge=1, le=40)
    date: str
    title: str
    description: str


class GoogleCalendarCreateRequest(BaseModel):
    events: List[CalendarEventItem]


class PregnancyPlanOutput(BaseModel):
    current_week: int = Field(..., ge=0, le=40)
    current_focus: str
    products: List[ProductItem] = Field(default_factory=list)
    next_2_weeks_preview: List[PreviewItem] = Field(default_factory=list)
    milestones: List[MilestoneItem] = Field(default_factory=list)
    calendar_advice: str
    calendar_events: List[CalendarEventItem] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_note: str
    full_timeline: Optional[List[PreviewItem]] = None
    debug: Optional[Dict[str, Any]] = None


SAFE_FALLBACK = PregnancyPlanOutput(
    current_week=0,
    current_focus="Unable to determine the current pregnancy stage safely. / تعذر تحديد مرحلة الحمل الحالية بشكل آمن.",
    products=[],
    next_2_weeks_preview=[],
    milestones=[],
    calendar_advice="Calendar integration unavailable. / تزامن التقويم غير متاح.",
    calendar_events=[],
    confidence=0.0,
    uncertainty_note="Please verify the due date and consult your doctor if you are unsure. / يرجى التحقق من موعد الولادة واستشارة الطبيب عند عدم التأكد.",
    full_timeline=None,
)
