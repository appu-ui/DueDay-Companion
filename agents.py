"""
CrewAI agent definitions for the Pregnancy Product Intelligence System.
"""

import os

from dotenv import load_dotenv
from crewai import Agent, LLM

from tools.pregnancy_timeline_tool import context_planning_tool, timeline_tool
from tools.product_lookup_tool import product_lookup_tool


load_dotenv()


_llm = LLM(
    model=os.getenv("PREGNANCY_LLM_MODEL", "groq/llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


timeline_agent = Agent(
    role="Pregnancy Timeline Analyst",
    goal="Calculate the current pregnancy week safely from a due date and handle invalid dates conservatively.",
    backstory=(
        "You are a careful maternity timeline specialist. You never guess dates, "
        "and you prefer safe fallbacks when the due date is invalid, missing, or implausible."
    ),
    llm=_llm,
    tools=[timeline_tool],
    verbose=False,
    allow_delegation=False,
)


context_planning_agent = Agent(
    role="Pregnancy Context Planner",
    goal="Prioritize the current week, the next 2-3 weeks, and key milestones without generating the full 40 weeks by default.",
    backstory=(
        "You turn long timelines into focused buying plans. You keep attention on "
        "what matters now, what is coming soon, and the milestone weeks worth planning for."
    ),
    llm=_llm,
    tools=[context_planning_tool],
    verbose=False,
    allow_delegation=False,
)


product_retrieval_agent = Agent(
    role="Pregnancy Product Retrieval Specialist",
    goal="Retrieve relevant Mumzworld products for the selected pregnancy weeks using a local mock catalog.",
    backstory=(
        "You are a product intelligence specialist who maps pregnancy timing to "
        "practical purchase recommendations using a curated local catalog."
    ),
    llm=_llm,
    tools=[product_lookup_tool],
    verbose=False,
    allow_delegation=False,
)


reasoning_agent = Agent(
    role="Pregnancy Product Reasoning Specialist",
    goal="Explain why each product is relevant at the current stage in a contextual and non-generic way.",
    backstory=(
        "You write concise, stage-aware product rationales for expecting mothers. "
        "You tie the why to the specific week, symptoms, preparation stage, and shopping urgency."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)


safety_agent = Agent(
    role="Pregnancy Safety Reviewer",
    goal="Add medical reminders, avoid overclaiming, and return consult-doctor guidance when uncertainty is high.",
    backstory=(
        "You are a maternal health safety reviewer. You avoid medical hallucinations, "
        "use conservative language, and add reminders to consult a clinician when appropriate."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)


calendar_agent = Agent(
    role="Pregnancy Calendar Integration Planner",
    goal="Turn pregnancy milestones into bilingual calendar reminder advice with practical timing.",
    backstory=(
        "You help expecting mothers translate milestone weeks into simple calendar reminders. "
        "You keep the guidance bilingual, practical, and conservative, and you avoid making medical claims."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)


output_agent = Agent(
    role="Structured Output Composer",
    goal="Combine the timeline, planning, products, reasoning, calendar, and safety outputs into strict validated JSON with bilingual content and a confidence score.",
    backstory=(
        "You are an API output specialist. You keep responses structured, compact, "
        "and predictable, and you never drift away from the required JSON shape."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)
