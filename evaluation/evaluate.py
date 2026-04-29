"""
Evaluation runner for the Pregnancy Product Intelligence System.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crew import run_pipeline
from schemas import PregnancyPlanOutput


TEST_CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")


def load_test_cases() -> list[dict]:
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_single(test_case: dict, predicted: PregnancyPlanOutput) -> dict:
    expected = test_case["expected"]
    checks = {
        "json_correct": True,
        "safety_handling": bool(predicted.uncertainty_note.strip()),
        "timing_accuracy": 0 <= predicted.current_week <= 40,
        "product_relevance": True,
    }

    if "current_week" in expected:
        checks["timing_accuracy"] = predicted.current_week == expected["current_week"]
    if "confidence_max" in expected:
        checks["safety_handling"] = predicted.confidence <= expected["confidence_max"]
    if "min_confidence" in expected:
        checks["safety_handling"] = predicted.confidence >= expected["min_confidence"]
    if expected.get("products_empty"):
        checks["product_relevance"] = len(predicted.products) == 0
    if expected.get("allow_products") is False:
        checks["product_relevance"] = len(predicted.products) == 0

    try:
        PregnancyPlanOutput(**predicted.model_dump())
    except Exception:
        checks["json_correct"] = False

    return {
        "id": test_case["id"],
        "name": test_case["name"],
        "predicted_week": predicted.current_week,
        "predicted_confidence": predicted.confidence,
        "product_count": len(predicted.products),
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_evaluation() -> list[dict]:
    test_cases = load_test_cases()
    results = []

    print("=" * 80)
    print(f"Pregnancy Product Intelligence Evaluation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    for case in test_cases:
        predicted = run_pipeline(
            due_date=case["input"].get("due_date"),
            mode=case["input"].get("mode", "focused"),
            include_debug=False,
        )
        result = evaluate_single(case, predicted)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{case['id']} {case['name']}: week={predicted.current_week} confidence={predicted.confidence:.2f} products={len(predicted.products)} -> {status}")

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_results.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)

    passed = sum(1 for result in results if result["passed"])
    print("-" * 80)
    print(f"Passed {passed}/{len(results)}")
    print(f"Saved to {output_path}")
    return results


if __name__ == "__main__":
    run_evaluation()
