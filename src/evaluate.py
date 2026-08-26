"""
Evaluation harness: runs every golden issue through the mock model
under a given prompt's detected feature set, and scores the result
against the real ground-truth severity (task.py) plus real,
deterministic checks on the summary's format compliance.

Two independent metrics, not one blended score, so a prompt that gets
severity right but produces bad-format summaries (or vice versa) is
visible rather than averaged away:
  - severity_accuracy: fraction of golden issues where the mock
    model's severity exactly matches expected_severity.
  - summary_format_compliance: fraction of golden issues where the
    summary (a) contains the site_id, (b) does not leak raw field
    names like "gap_days=" or "issue=", and (c) is a single sentence
    (ends with exactly one '.' at the very end, no internal '. ').
"""

import re

from mock_llm import run_mock_llm
from prompts import detect_prompt_features
from task import GOLDEN_ISSUES


def _summary_contains_site_id(summary, site_id):
    return site_id in summary


def _summary_leaks_raw_fields(summary):
    return bool(re.search(r"\b(gap_days|max_allowed_days|issue|occurrences)\s*=", summary))


def _summary_is_single_sentence(summary):
    stripped = summary.strip()
    if not stripped.endswith("."):
        return False
    # No '. ' (period followed by a space) before the final character
    # -- that would indicate a second sentence.
    body = stripped[:-1]
    return ". " not in body


def evaluate_prompt(prompt_text, golden_issues=None):
    """
    Run the mock model over every golden issue under this prompt's
    detected features, and return per-issue results plus aggregate
    metrics.
    """
    golden_issues = golden_issues if golden_issues is not None else GOLDEN_ISSUES
    features = detect_prompt_features(prompt_text)

    results = []
    for issue in golden_issues:
        output = run_mock_llm(issue, features)
        severity_correct = output["severity"] == issue["expected_severity"]
        format_ok = (
            _summary_contains_site_id(output["summary"], issue["site_id"])
            and not _summary_leaks_raw_fields(output["summary"])
            and _summary_is_single_sentence(output["summary"])
        )
        results.append({
            "site_id": issue["site_id"],
            "issue_type": issue["issue"],
            "expected_severity": issue["expected_severity"],
            "predicted_severity": output["severity"],
            "severity_correct": severity_correct,
            "summary": output["summary"],
            "summary_format_ok": format_ok,
        })

    n = len(results)
    severity_accuracy = sum(r["severity_correct"] for r in results) / n
    summary_format_compliance = sum(r["summary_format_ok"] for r in results) / n

    return {
        "detected_features": features,
        "results": results,
        "severity_accuracy": severity_accuracy,
        "summary_format_compliance": summary_format_compliance,
        "n_issues": n,
    }


def compare_prompt_versions(prompt_versions, golden_issues=None):
    """
    Evaluate every prompt version and return a dict of
    {version_name: evaluation_result}, in the order given.
    """
    return {
        name: evaluate_prompt(text, golden_issues)
        for name, text in prompt_versions.items()
    }
