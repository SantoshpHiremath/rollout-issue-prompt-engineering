import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from evaluate import evaluate_prompt, compare_prompt_versions
from prompts import PROMPT_VERSIONS
from task import GOLDEN_ISSUES


def test_evaluate_prompt_covers_all_golden_issues():
    result = evaluate_prompt(PROMPT_VERSIONS["v1_bare"])
    assert result["n_issues"] == len(GOLDEN_ISSUES)
    assert len(result["results"]) == len(GOLDEN_ISSUES)


def test_evaluate_prompt_accuracy_is_valid_fraction():
    for name, text in PROMPT_VERSIONS.items():
        result = evaluate_prompt(text)
        assert 0.0 <= result["severity_accuracy"] <= 1.0
        assert 0.0 <= result["summary_format_compliance"] <= 1.0


def test_severity_accuracy_strictly_improves_from_v1_to_v3():
    """
    The core claim of this project: each added prompt feature (severity
    definitions, then a worked SLA-magnitude example) measurably
    improves severity accuracy against the golden set. This is checked
    directly, not asserted -- if a future prompt edit regresses this,
    the test fails.
    """
    results = compare_prompt_versions(PROMPT_VERSIONS)
    v1_acc = results["v1_bare"]["severity_accuracy"]
    v2_acc = results["v2_with_definitions"]["severity_accuracy"]
    v3_acc = results["v3_with_worked_example"]["severity_accuracy"]
    assert v1_acc < v2_acc < v3_acc


def test_v3_achieves_perfect_severity_accuracy_on_golden_set():
    result = evaluate_prompt(PROMPT_VERSIONS["v3_with_worked_example"])
    assert result["severity_accuracy"] == 1.0


def test_format_compliance_only_reaches_full_with_v4():
    results = compare_prompt_versions(PROMPT_VERSIONS)
    assert results["v1_bare"]["summary_format_compliance"] < 1.0
    assert results["v2_with_definitions"]["summary_format_compliance"] < 1.0
    assert results["v3_with_worked_example"]["summary_format_compliance"] < 1.0
    assert results["v4_with_output_schema"]["summary_format_compliance"] == 1.0


def test_v4_achieves_perfect_scores_on_both_metrics():
    result = evaluate_prompt(PROMPT_VERSIONS["v4_with_output_schema"])
    assert result["severity_accuracy"] == 1.0
    assert result["summary_format_compliance"] == 1.0


def test_compare_prompt_versions_preserves_order():
    results = compare_prompt_versions(PROMPT_VERSIONS)
    assert list(results.keys()) == list(PROMPT_VERSIONS.keys())


def test_evaluate_prompt_works_with_a_custom_golden_subset():
    subset = GOLDEN_ISSUES[:3]
    result = evaluate_prompt(PROMPT_VERSIONS["v4_with_output_schema"], golden_issues=subset)
    assert result["n_issues"] == 3
