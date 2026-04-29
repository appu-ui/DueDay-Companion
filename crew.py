"""
Crew orchestration for the Pregnancy Product Intelligence System.
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timedelta

from crewai import Crew, Process

from agents import (
    calendar_agent,
    context_planning_agent,
    output_agent,
    product_retrieval_agent,
    reasoning_agent,
    safety_agent,
    timeline_agent,
)
from schemas import PregnancyPlanOutput, SAFE_FALLBACK
from tasks import (
    calendar_task,
    context_planning_task,
    output_task,
    product_retrieval_task,
    reasoning_task,
    safety_task,
    timeline_task,
)
from tools.pregnancy_timeline_tool import build_context_plan, calculate_pregnancy_timeline
from tools.product_lookup_tool import get_products_for_week


MILESTONE_EVENTS = {
    12: "First trimester check-in and symptom support / متابعة نهاية الثلث الأول ودعم الأعراض",
    20: "Mid-pregnancy anatomy planning and comfort upgrades / تخطيط فحص منتصف الحمل وتحسين الراحة",
    28: "Third-trimester prep begins / بداية الاستعداد للثلث الثالث",
    32: "Nursery and feeding setup review / مراجعة تجهيزات الطفل والرضاعة",
    36: "Hospital bag and birth readiness / تجهيز حقيبة المستشفى والاستعداد للولادة",
    40: "Final waiting period and essential-only shopping / الفترة الأخيرة والاكتفاء بالأساسيات",
}


pregnancy_crew = Crew(
    agents=[
        timeline_agent,
        context_planning_agent,
        product_retrieval_agent,
        reasoning_agent,
        safety_agent,
        calendar_agent,
        output_agent,
    ],
    tasks=[
        timeline_task,
        context_planning_task,
        product_retrieval_task,
        reasoning_task,
        safety_task,
        calendar_task,
        output_task,
    ],
    process=Process.sequential,
    verbose=False,
)


def _extract_json_from_text(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                return None
    return None


def _build_retrieval_seed(context_plan: dict) -> dict:
    current_bundle = get_products_for_week(context_plan["current_week"])
    preview_bundles = [get_products_for_week(week) for week in context_plan["preview_weeks"]]
    milestones = [
        {
            "week": week,
            "event": MILESTONE_EVENTS.get(week, f"Week {week} planning milestone / محطة تخطيط للأسبوع {week}"),
        }
        for week in context_plan["milestone_weeks"]
    ]
    full_timeline_bundles = []
    for week in context_plan.get("full_timeline_weeks", []):
        full_timeline_bundles.append(get_products_for_week(week))

    return {
        "current_week_bundle": current_bundle,
        "preview_bundles": preview_bundles,
        "milestones": milestones,
        "full_timeline_bundles": full_timeline_bundles,
    }


def _milestone_date(timeline_seed: dict, milestone_week: int) -> str | None:
    due_date_text = timeline_seed.get("due_date")
    if not due_date_text:
        return None
    try:
        due_date = datetime.strptime(due_date_text, "%Y-%m-%d").date()
    except ValueError:
        return None

    pregnancy_start = due_date - timedelta(days=280)
    reminder_date = pregnancy_start + timedelta(days=(int(milestone_week) - 1) * 7)
    return reminder_date.isoformat()


def _build_calendar_seed(timeline_seed: dict, milestones: list[dict]) -> dict:
    return {
        "current_week": timeline_seed["current_week"],
        "due_date": timeline_seed.get("due_date"),
        "milestones": [
            {
                "week": item["week"],
                "event": item["event"],
                "suggested_date": _milestone_date(timeline_seed, item["week"]),
            }
            for item in milestones
        ],
    }


def _build_calendar_advice(calendar_seed: dict) -> str:
    milestones = calendar_seed.get("milestones", [])
    if not milestones:
        return (
            "No upcoming milestone reminders were identified; keep routine prenatal appointments in your calendar. / "
            "لم يتم تحديد تذكيرات مراحل قادمة؛ احتفظي بمواعيد متابعة الحمل الروتينية في التقويم."
        )

    reminder_parts = []
    for item in milestones:
        date_text = item.get("suggested_date") or "date to confirm"
        reminder_parts.append(f"week {item['week']} on {date_text}: {item['event']}")

    return (
        "Add calendar reminders for "
        + "; ".join(reminder_parts)
        + ". Confirm appointment timing with your doctor. / أضيفي تذكيرات في التقويم لهذه المراحل، وتأكدي من توقيت المواعيد مع طبيبك."
    )


def _build_calendar_events(calendar_seed: dict) -> list[dict]:
    events = []
    for item in calendar_seed.get("milestones", []):
        date_text = item.get("suggested_date")
        if not date_text:
            continue
        event_text = item["event"]
        event_en = event_text.split(" / ", 1)[0]
        events.append(
            {
                "week": item["week"],
                "date": date_text,
                "title": f"Pregnancy week {item['week']}: {event_en}",
                "description": (
                    f"{event_text}\n\n"
                    "Generated by Cry to Clarity. Confirm appointment timing with your doctor."
                ),
            }
        )
    return events


def _fallback_with_debug(debug_payload: dict | None = None, include_debug: bool = False) -> PregnancyPlanOutput:
    if not include_debug:
        return SAFE_FALLBACK
    payload = SAFE_FALLBACK.model_dump()
    payload["debug"] = debug_payload
    return PregnancyPlanOutput(**payload)


def _build_deterministic_plan(
    timeline_seed: dict,
    context_seed: dict,
    retrieval_seed: dict,
    calendar_seed: dict,
    include_debug: bool = False,
    debug_payload: dict | None = None,
) -> PregnancyPlanOutput:
    current_bundle = retrieval_seed["current_week_bundle"]
    preview = [
        {
            "week": bundle["week"],
            "focus": f"{bundle['focus_en']} / {bundle['focus_ar']}",
            "buy": [product["name"] for product in bundle["products"]],
        }
        for bundle in retrieval_seed["preview_bundles"]
    ]
    milestones = retrieval_seed["milestones"]
    products = [
        {
            "name": product["name"],
            "url": product["url"],
            "reason": {
                "en": f"{product['base_reason_en']} This is timely for week {timeline_seed['current_week']}.",
                "ar": f"{product['base_reason_ar']} وهذا مناسب للأسبوع {timeline_seed['current_week']}.",
            },
            "timing": product["timing"],
        }
        for product in current_bundle["products"]
    ]
    full_timeline = None
    if context_seed.get("mode") == "full_timeline":
        full_timeline = [
            {
                "week": bundle["week"],
                "focus": f"{bundle['focus_en']} / {bundle['focus_ar']}",
                "buy": [product["name"] for product in bundle["products"]],
            }
            for bundle in retrieval_seed["full_timeline_bundles"]
        ]

    result = PregnancyPlanOutput(
        current_week=timeline_seed["current_week"],
        current_focus=f"{current_bundle['focus_en']} / {current_bundle['focus_ar']}",
        products=products,
        next_2_weeks_preview=preview,
        milestones=[
            {
                "week": item["week"],
                "event": item["event"],
            }
            for item in milestones
        ],
        calendar_advice=_build_calendar_advice(calendar_seed),
        calendar_events=_build_calendar_events(calendar_seed),
        confidence=0.76,
        uncertainty_note=(
            "Generated from deterministic planning rules and the mock catalog; consult doctor for medical decisions. / "
            "تم إنشاء الخطة من قواعد تخطيط ثابتة وكتالوج تجريبي؛ يرجى استشارة الطبيب في القرارات الطبية."
        ),
        full_timeline=full_timeline,
        debug=debug_payload if include_debug else None,
    )
    return result


def _parse_crew_results(
    crew_output,
    timeline_seed: dict,
    context_seed: dict,
    retrieval_seed: dict,
    calendar_seed: dict,
    include_debug: bool = False,
) -> PregnancyPlanOutput:
    task_outputs = crew_output.tasks_output
    debug_payload = {
        "timeline_seed": timeline_seed,
        "retrieval_seed": retrieval_seed,
        "calendar_seed": calendar_seed,
        "crew_tasks": [],
    }
    for index, output in enumerate(task_outputs):
        debug_payload["crew_tasks"].append(
            {
                "index": index,
                "name": getattr(output, "name", None),
                "raw": output.raw,
                "parsed_json": _extract_json_from_text(output.raw),
            }
        )

    final_data = _extract_json_from_text(task_outputs[-1].raw)
    if not final_data:
        return _build_deterministic_plan(timeline_seed, context_seed, retrieval_seed, calendar_seed, include_debug, debug_payload)

    try:
        final_data.setdefault("calendar_events", _build_calendar_events(calendar_seed))
        result = PregnancyPlanOutput(**final_data)
        if include_debug:
            result.debug = debug_payload
        return result
    except Exception:
        return _build_deterministic_plan(timeline_seed, context_seed, retrieval_seed, calendar_seed, include_debug, debug_payload)


def build_safe_error_response(error_code: str, message_en: str, message_ar: str) -> PregnancyPlanOutput:
    payload = SAFE_FALLBACK.model_dump()
    payload["current_focus"] = f"{message_en} / {message_ar}"
    payload["uncertainty_note"] = f"{message_en} Please consult doctor if unsure. / {message_ar} يرجى استشارة الطبيب عند عدم التأكد."
    payload["debug"] = {"error_code": error_code}
    return PregnancyPlanOutput(**payload)


def run_pipeline(due_date: str | None, mode: str = "focused", include_debug: bool = False) -> PregnancyPlanOutput:
    try:
        timeline_seed = calculate_pregnancy_timeline(due_date or "")
        if not timeline_seed.get("ok"):
            errors = {
                "missing_due_date": (
                    "Due date is required to generate a pregnancy plan.",
                    "موعد الولادة مطلوب لإنشاء خطة الحمل.",
                ),
                "invalid_due_date": (
                    "Due date format is invalid. Use YYYY-MM-DD.",
                    "تنسيق موعد الولادة غير صالح. استخدمي الصيغة YYYY-MM-DD.",
                ),
                "past_due_date": (
                    "Due date is in the past, so the plan cannot be generated safely.",
                    "موعد الولادة في الماضي، لذلك لا يمكن إنشاء الخطة بشكل آمن.",
                ),
                "far_future_due_date": (
                    "Due date is unusually far in the future. Please confirm it before planning.",
                    "موعد الولادة بعيد بشكل غير معتاد. يرجى تأكيده قبل التخطيط.",
                ),
            }
            message_en, message_ar = errors.get(
                timeline_seed.get("error", ""),
                ("Unable to validate the due date safely.", "تعذر التحقق من موعد الولادة بشكل آمن."),
            )
            result = build_safe_error_response(timeline_seed.get("error", "timeline_error"), message_en, message_ar)
            if not include_debug:
                result.debug = None
            else:
                result.debug = {"timeline_seed": timeline_seed}
            return result

        context_seed = build_context_plan(timeline_seed["current_week"], mode)
        retrieval_seed = _build_retrieval_seed(context_seed)
        calendar_seed = _build_calendar_seed(timeline_seed, retrieval_seed["milestones"])

        crew_output = pregnancy_crew.kickoff(
            inputs={
                "request_json": json.dumps({"due_date": due_date, "mode": mode}),
                "timeline_seed_json": json.dumps(timeline_seed, ensure_ascii=False),
                "context_seed_json": json.dumps(context_seed, ensure_ascii=False),
                "retrieval_seed_json": json.dumps(retrieval_seed, ensure_ascii=False),
                "calendar_seed_json": json.dumps(calendar_seed, ensure_ascii=False),
            }
        )

        return _parse_crew_results(
            crew_output,
            timeline_seed=timeline_seed,
            context_seed=context_seed,
            retrieval_seed=retrieval_seed,
            calendar_seed=calendar_seed,
            include_debug=include_debug,
        )
    except Exception as exc:
        print(f"[Pipeline] ERROR: {exc}")
        traceback.print_exc()
        if "timeline_seed" in locals() and timeline_seed.get("ok"):
            context_seed = locals().get("context_seed") or build_context_plan(timeline_seed["current_week"], mode)
            retrieval_seed = locals().get("retrieval_seed") or _build_retrieval_seed(context_seed)
            calendar_seed = locals().get("calendar_seed") or _build_calendar_seed(timeline_seed, retrieval_seed["milestones"])
            return _build_deterministic_plan(
                timeline_seed,
                context_seed,
                retrieval_seed,
                calendar_seed,
                include_debug=include_debug,
                debug_payload={"exception": str(exc)},
            )
        return _fallback_with_debug({"exception": str(exc)}, include_debug)
