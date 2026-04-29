"""
Local product retrieval for the Pregnancy Product Intelligence System.
"""

from __future__ import annotations

import json
import os

from crewai.tools import tool


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PRODUCTS_PATH = os.path.join(_DATA_DIR, "pregnancy_products.json")


def _load_catalog() -> list[dict]:
    with open(_PRODUCTS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_stage_bundle(week: int) -> dict:
    catalog = _load_catalog()
    ordered = sorted(catalog, key=lambda item: item["start_week"])
    selected = ordered[-1]
    for item in ordered:
        if item["start_week"] <= week <= item["end_week"]:
            selected = item
            break
        if week >= item["start_week"]:
            selected = item
    return selected


def get_products_for_week(week: int) -> dict:
    stage = get_stage_bundle(week)
    return {
        "week": week,
        "focus_en": stage["focus_en"],
        "focus_ar": stage["focus_ar"],
        "products": stage["products"],
    }


@tool("Pregnancy Product Lookup Tool")
def product_lookup_tool(week: int) -> str:
    """Retrieve pregnancy products for a given week from the local catalog."""
    return json.dumps(get_products_for_week(int(week)), ensure_ascii=False)
