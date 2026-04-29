"""
CrewAI task definitions for the Pregnancy Product Intelligence System.
"""

from crewai import Task

from agents import (
    calendar_agent,
    context_planning_agent,
    output_agent,
    product_retrieval_agent,
    reasoning_agent,
    safety_agent,
    timeline_agent,
)


timeline_task = Task(
    description=(
        "Determine the pregnancy timeline safely for the following request:\n\n"
        "{request_json}\n\n"
        "Deterministic timeline seed:\n{timeline_seed_json}\n\n"
        "Use the Pregnancy Timeline Tool only if you need to verify the seed. Return ONLY valid JSON in this format:\n"
        '{"ok": true, "current_week": 24, "trimester": 2, "days_until_due": 112}\n'
        "If invalid or unsafe, return:\n"
        '{"ok": false, "error": "...", "message": "..."}'
    ),
    expected_output='A JSON object describing whether the due date is valid and, if so, the current pregnancy week.',
    agent=timeline_agent,
)


context_planning_task = Task(
    description=(
        "Use the timeline result from the previous step plus the request mode to create a focused planning scope.\n\n"
        "Deterministic planning seed:\n{context_seed_json}\n\n"
        "Rules:\n"
        "1. Do not generate all 40 weeks unless mode is full_timeline\n"
        "2. Include current week\n"
        "3. Include next 2-3 weeks preview\n"
        "4. Include important milestone weeks\n\n"
        "Return ONLY valid JSON in this format:\n"
        '{"mode": "focused", "current_week": 24, "preview_weeks": [25, 26], "milestone_weeks": [28, 32, 36], "selected_weeks": [24, 25, 26]}'
    ),
    expected_output="A JSON object with the selected weeks to cover.",
    agent=context_planning_agent,
    context=[timeline_task],
)


product_retrieval_task = Task(
    description=(
        "Use the planning scope from the previous task and the Pregnancy Product Lookup Tool to fetch relevant products.\n\n"
        "Deterministic retrieval seed:\n{retrieval_seed_json}\n\n"
        "Return ONLY valid JSON in this format:\n"
        '{"current_week_bundle": {"week": 24, "focus_en": "...", "focus_ar": "...", "products": [{"name": "...", "timing": "...", "base_reason_en": "...", "base_reason_ar": "..."}]}, "preview_bundles": [{"week": 25, "focus_en": "...", "focus_ar": "...", "products": []}], "milestones": [{"week": 28, "event_en": "...", "event_ar": "..."}], "full_timeline_bundles": []}'
    ),
    expected_output="A JSON object containing current products, preview bundles, and milestone metadata.",
    agent=product_retrieval_agent,
    context=[context_planning_task],
)


reasoning_task = Task(
    description=(
        "Use the current week product bundle to explain why each product is relevant right now.\n\n"
        "Requirements:\n"
        "1. Reasons must be stage-aware and specific to the current week\n"
        "2. Provide English and Arabic for each product\n"
        "3. Keep each reason concise and practical\n\n"
        "Return ONLY valid JSON in this format:\n"
        '{"current_focus": "... / ...", "products": [{"name": "...", "reason": {"en": "...", "ar": "..."}, "timing": "..."}], "next_2_weeks_preview": [{"week": 25, "focus": "... / ...", "buy": ["..."]}], "milestones": [{"week": 28, "event": "... / ..."}], "full_timeline": []}'
    ),
    expected_output="A JSON object with enriched product reasoning and preview content.",
    agent=reasoning_agent,
    context=[product_retrieval_task],
)


safety_task = Task(
    description=(
        "Review the proposed plan for safety.\n\n"
        "Rules:\n"
        "1. Do not give medical diagnosis\n"
        "2. If any medical uncertainty exists, say consult doctor\n"
        "3. Keep safety reminders realistic and non-alarmist\n"
        "4. Confidence must be lower for uncertain, invalid, missing, or far-future inputs\n\n"
        "Return ONLY valid JSON in this format:\n"
        '{"confidence": 0.84, "uncertainty_note": "... / ..."}'
    ),
    expected_output="A JSON object with confidence and uncertainty note.",
    agent=safety_agent,
    context=[timeline_task, reasoning_task],
)


calendar_task = Task(
    description=(
        "Use the timeline and milestone outputs to create bilingual calendar integration advice.\n\n"
        "Deterministic calendar seed:\n{calendar_seed_json}\n\n"
        "Rules:\n"
        "1. Mention the milestone week, event, and suggested reminder date when available\n"
        "2. Recommend adding reminders to the user's calendar, not actually creating external calendar events\n"
        "3. Keep the advice concise, practical, and bilingual English / Arabic\n"
        "4. Include consult-doctor language for clinical appointments or uncertainty\n\n"
        "Return ONLY valid JSON in this format:\n"
        '{"calendar_advice": "Add calendar reminders for week 28 on 2026-07-01: Third-trimester prep begins. / ..."}'
    ),
    expected_output="A JSON object with bilingual calendar advice for upcoming pregnancy milestones.",
    agent=calendar_agent,
    context=[timeline_task, context_planning_task, reasoning_task],
)


output_task = Task(
    description=(
        "Combine all validated outputs into STRICT final JSON.\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        '{'
        '"current_week": 24, '
        '"current_focus": "...", '
        '"products": [{"name": "...", "url": "https://www.mumzworld.com/en/...", "reason": {"en": "...", "ar": "..."}, "timing": "..."}], '
        '"next_2_weeks_preview": [{"week": 25, "focus": "...", "buy": []}], '
        '"milestones": [{"week": 28, "event": "..."}], '
        '"calendar_advice": "... / ...", '
        '"confidence": 0.84, '
        '"uncertainty_note": "...", '
        '"full_timeline": []'
        '}'
    ),
    expected_output="A final JSON object matching the response schema.",
    agent=output_agent,
    context=[timeline_task, reasoning_task, safety_task, calendar_task],
)
