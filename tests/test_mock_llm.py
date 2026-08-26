import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mock_llm import run_mock_llm


NO_FEATURES = {
    "has_severity_definitions": False,
    "has_sla_magnitude_example": False,
    "has_output_schema": False,
}

ALL_FEATURES = {
    "has_severity_definitions": True,
    "has_sla_magnitude_example": True,
    "has_output_schema": True,
}


def test_baseline_out_of_order_is_underrated_without_definitions():
    """
    Documents the deliberate baseline weakness: without severity
    definitions, the mock model defaults out_of_order to "Hoch" even
    though the correct answer is "Kritisch" -- this is what makes v1's
    low accuracy score meaningful rather than arbitrary.
    """
    issue = {"issue": "out_of_order", "site_id": "SITE-1"}
    result = run_mock_llm(issue, NO_FEATURES)
    assert result["severity"] == "Hoch"


def test_with_definitions_out_of_order_is_correctly_kritisch():
    issue = {"issue": "out_of_order", "site_id": "SITE-1"}
    result = run_mock_llm(issue, {**NO_FEATURES, "has_severity_definitions": True})
    assert result["severity"] == "Kritisch"


def test_sla_breach_ignores_magnitude_without_the_worked_example():
    issue = {"issue": "sla_breach", "site_id": "SITE-1", "gap_days": 500, "max_allowed_days": 10}
    result = run_mock_llm(issue, {**NO_FEATURES, "has_severity_definitions": True})
    # Baseline SLA handling (post-definitions but pre-worked-example)
    # still just says "Hoch" regardless of how extreme the overrun is.
    assert result["severity"] == "Hoch"


def test_sla_breach_applies_2x_threshold_with_worked_example():
    issue = {"issue": "sla_breach", "site_id": "SITE-1", "gap_days": 500, "max_allowed_days": 10}
    result = run_mock_llm(issue, ALL_FEATURES)
    assert result["severity"] == "Kritisch"


def test_sla_breach_stays_hoch_when_under_threshold_with_worked_example():
    issue = {"issue": "sla_breach", "site_id": "SITE-1", "gap_days": 15, "max_allowed_days": 10}
    result = run_mock_llm(issue, ALL_FEATURES)
    assert result["severity"] == "Hoch"  # 15 <= 2*10


def test_summary_leaks_raw_fields_without_output_schema():
    issue = {"issue": "sla_breach", "site_id": "SITE-99", "gap_days": 50,
              "max_allowed_days": 10, "milestone": "Bau"}
    result = run_mock_llm(issue, NO_FEATURES)
    assert "gap_days=" in result["summary"]


def test_summary_is_clean_with_output_schema():
    issue = {"issue": "sla_breach", "site_id": "SITE-99", "gap_days": 50,
              "max_allowed_days": 10, "milestone": "Bau", "prerequisite": "Genehmigung"}
    result = run_mock_llm(issue, ALL_FEATURES)
    assert "gap_days=" not in result["summary"]
    assert "SITE-99" in result["summary"]


def test_summary_always_returns_a_string_for_every_issue_type():
    for issue_type in ["sla_breach", "out_of_order", "missing_date", "duplicate"]:
        issue = {"issue": issue_type, "site_id": "SITE-X", "occurrences": 2}
        result = run_mock_llm(issue, ALL_FEATURES)
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0
