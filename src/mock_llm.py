"""
A deterministic mock LLM standing in for a real model call.

This is a rule-based stand-in for a language model, not a real model.
The project's value is the reusable measurement methodology (prompt
versions, a golden evaluation set, a scoring harness), which is fully
exercised and tested against this stand-in; a real model client can
replace it without changing the harness.

To make this a genuine test of PROMPT QUALITY rather than a rigged
puzzle, the mock model is built to behave the way an actual small
instruction-following model plausibly would: it doesn't have access to
the ground-truth severity rules in task.py. Instead, it has its own
independent, cruder heuristics for guessing severity and phrasing a
summary -- heuristics that only align well with the real rules when the
PROMPT ITSELF supplies enough explicit structure (a severity
definition, few-shot examples, an explicit output schema) to compensate
for the model's own weak default judgment. A prompt that just says
"classify the severity" leaves the mock model to guess with its own
crude defaults and get many wrong -- exactly what happens with a real
small model given an underspecified prompt.
"""

import re


def _extract_field(issue, key, default=None):
    return issue.get(key, default)


def _mock_severity_guess(issue, prompt_features):
    """
    The mock model's own (imperfect) severity judgment. Its accuracy
    depends on which prompt features are present -- this is the
    mechanism that makes prompt iteration actually matter, rather than
    being cosmetic.
    """
    issue_type = issue["issue"]

    # Baseline (weak) heuristic available with NO prompt guidance at
    # all: the model just pattern-matches on the issue-type string and
    # picks something plausible-sounding, ignoring magnitude entirely.
    baseline_guess = {
        "sla_breach": "Hoch",       # ignores how far over the SLA it is
        "out_of_order": "Hoch",     # underrates this -- doesn't know it should be Kritisch
        "missing_date": "Niedrig",  # underrates this -- doesn't know it should be Hoch
        "duplicate": "Hoch",        # overrates this -- doesn't know it's low-urgency
    }[issue_type]

    guess = baseline_guess

    # Feature: explicit severity definitions in the prompt (what
    # "Kritisch" vs "Hoch" vs "Niedrig" actually means) lets the model
    # correct out_of_order and duplicate, which the baseline gets wrong.
    if prompt_features.get("has_severity_definitions"):
        if issue_type == "out_of_order":
            guess = "Kritisch"
        if issue_type == "duplicate":
            guess = "Niedrig"
        if issue_type == "missing_date":
            guess = "Hoch"

    # Feature: a worked few-shot example showing the SLA-breach
    # magnitude threshold (2x max_allowed_days) lets the model apply
    # that threshold to new cases, rather than defaulting sla_breach to
    # a flat "Hoch" regardless of how bad the overrun is.
    if prompt_features.get("has_sla_magnitude_example") and issue_type == "sla_breach":
        gap = _extract_field(issue, "gap_days")
        max_allowed = _extract_field(issue, "max_allowed_days")
        if gap is not None and max_allowed is not None:
            guess = "Kritisch" if gap > 2 * max_allowed else "Hoch"

    return guess


def _mock_summary(issue, prompt_features):
    """
    The mock model's summary-writing behavior. Without an explicit
    output-format constraint, it sometimes produces a summary that's
    too long, includes internal field names verbatim (like a raw
    system talking to itself instead of a human-readable sentence), or
    omits the site_id -- all realistic small-model failure modes for
    an underspecified prompt.
    """
    site_id = issue["site_id"]
    issue_type = issue["issue"]

    if not prompt_features.get("has_output_schema"):
        # Underspecified: sometimes leaks raw field names, sometimes
        # forgets the site_id, sometimes rambles past one sentence.
        if issue_type == "sla_breach":
            return (f"issue=sla_breach gap_days={issue.get('gap_days')} "
                     f"max_allowed_days={issue.get('max_allowed_days')} "
                     f"milestone={issue.get('milestone')} bei diesem Standort, "
                     f"was bedeutet, dass die Anforderung nicht eingehalten wurde "
                     f"und das Team das bitte prüfen sollte, da es sich um eine "
                     f"Verzögerung handelt die Auswirkungen haben könnte.")
        if issue_type == "duplicate":
            return f"Duplikat gefunden. occurrences={issue.get('occurrences')}."
        if issue_type == "missing_date":
            return f"Datum fehlt für {issue.get('milestone')}."
        if issue_type == "out_of_order":
            return "Reihenfolge stimmt nicht."

    # With an explicit schema constraint ("one plain-German sentence,
    # must include the site_id, no raw field names"), the mock model
    # complies with that structure.
    templates = {
        "sla_breach": (
            f"Standort {site_id}: Die Anforderung zwischen {issue.get('prerequisite')} "
            f"und {issue.get('milestone')} wurde um {issue.get('gap_days')} Tage "
            f"überschritten (erlaubt: {issue.get('max_allowed_days')} Tage)."
        ),
        "out_of_order": (
            f"Standort {site_id}: Der Meilenstein {issue.get('milestone')} ist vor "
            f"seiner Voraussetzung {issue.get('prerequisite')} datiert und sollte "
            f"korrigiert werden."
        ),
        "missing_date": (
            f"Standort {site_id}: Für den aktuellen Meilenstein "
            f"{issue.get('milestone')} fehlt das Datum."
        ),
        "duplicate": (
            f"Standort {site_id}: Der Standort ist {issue.get('occurrences')}-fach "
            f"in den Daten vorhanden und sollte dedupliziert werden."
        ),
    }
    return templates[issue_type]


def run_mock_llm(issue, prompt_features):
    """
    Simulate what a small instruction-following model would produce
    for this issue, given which structural features the prompt
    contains. Returns {"severity": ..., "summary": ...}, mirroring the
    real output shape a live model call would return.
    """
    return {
        "severity": _mock_severity_guess(issue, prompt_features),
        "summary": _mock_summary(issue, prompt_features),
    }
