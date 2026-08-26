"""
The actual prompt versions being iterated and compared. Each is real,
complete prompt text (not a stub) that would be sent as the system/
instruction prompt to an LLM given one issue record as input.

detect_prompt_features() parses the REAL PROMPT TEXT (not a hidden
version tag) to decide which structural features are present -- this
matters: the mock model's behavior in mock_llm.py responds to detected
features, not to a version number, so a hand-edited or reordered prompt
genuinely changes the outcome instead of the harness silently keying
off "which version is this."
"""

import re

PROMPT_V1 = """\
Du bist ein Assistent für ein Mobilfunk-Rollout-Team.
Klassifiziere die Dringlichkeit des folgenden Datenproblems und fasse es zusammen.

Problem: {issue}
"""

PROMPT_V2 = """\
Du bist ein Assistent für ein Mobilfunk-Rollout-Team.
Klassifiziere die Dringlichkeit des folgenden Datenproblems (Kritisch, Hoch oder Niedrig)
und fasse es in einem Satz zusammen.

Dringlichkeits-Definitionen:
- Kritisch: blockiert den Rollout oder deutet auf einen schwerwiegenden Datenfehler hin
  (z. B. eine unmögliche Meilenstein-Reihenfolge, oder eine SLA-Überschreitung um mehr
  als das Doppelte der erlaubten Frist).
- Hoch: verletzt eine Anforderung/SLA, blockiert aber nicht sofort den Rollout
  (z. B. eine moderate SLA-Überschreitung, oder ein fehlendes Datum).
- Niedrig: stört nicht den Rollout-Fortschritt (z. B. ein doppelter Dateneintrag).

Problem: {issue}
"""

PROMPT_V3 = """\
Du bist ein Assistent für ein Mobilfunk-Rollout-Team.
Klassifiziere die Dringlichkeit des folgenden Datenproblems (Kritisch, Hoch oder Niedrig)
und fasse es in einem Satz zusammen.

Dringlichkeits-Definitionen:
- Kritisch: blockiert den Rollout oder deutet auf einen schwerwiegenden Datenfehler hin
  (z. B. eine unmögliche Meilenstein-Reihenfolge, oder eine SLA-Überschreitung um mehr
  als das Doppelte der erlaubten Frist).
- Hoch: verletzt eine Anforderung/SLA, blockiert aber nicht sofort den Rollout
  (z. B. eine moderate SLA-Überschreitung, oder ein fehlendes Datum).
- Niedrig: stört nicht den Rollout-Fortschritt (z. B. ein doppelter Dateneintrag).

Beispiel für die SLA-Schwelle (Faktor 2x):
  gap_days=95, max_allowed_days=30 -> 95 > 2*30=60 -> Kritisch
  gap_days=70, max_allowed_days=60 -> 70 <= 2*60=120 -> Hoch

Problem: {issue}
"""

PROMPT_V4 = """\
Du bist ein Assistent für ein Mobilfunk-Rollout-Team.
Klassifiziere die Dringlichkeit des folgenden Datenproblems (Kritisch, Hoch oder Niedrig)
und fasse es in GENAU EINEM Satz auf Deutsch zusammen.

Dringlichkeits-Definitionen:
- Kritisch: blockiert den Rollout oder deutet auf einen schwerwiegenden Datenfehler hin
  (z. B. eine unmögliche Meilenstein-Reihenfolge, oder eine SLA-Überschreitung um mehr
  als das Doppelte der erlaubten Frist).
- Hoch: verletzt eine Anforderung/SLA, blockiert aber nicht sofort den Rollout
  (z. B. eine moderate SLA-Überschreitung, oder ein fehlendes Datum).
- Niedrig: stört nicht den Rollout-Fortschritt (z. B. ein doppelter Dateneintrag).

Beispiel für die SLA-Schwelle (Faktor 2x):
  gap_days=95, max_allowed_days=30 -> 95 > 2*30=60 -> Kritisch
  gap_days=70, max_allowed_days=60 -> 70 <= 2*60=120 -> Hoch

Ausgabeformat (STRIKT einhalten):
- Der Satz muss die Standort-ID (site_id) enthalten.
- Der Satz darf KEINE internen Feldnamen (z. B. "gap_days", "issue=") enthalten
  -- schreibe stattdessen in normaler, verständlicher Sprache.
- Genau EIN Satz, keine Aufzählung, keine mehrfachen Sätze.

Problem: {issue}
"""

PROMPT_VERSIONS = {
    "v1_bare": PROMPT_V1,
    "v2_with_definitions": PROMPT_V2,
    "v3_with_worked_example": PROMPT_V3,
    "v4_with_output_schema": PROMPT_V4,
}


def detect_prompt_features(prompt_text):
    """
    Parse the real prompt text to determine which structural features
    are present. This drives the mock model's behavior (see
    mock_llm.py) -- so a hand-edited prompt genuinely changes the
    simulated outcome rather than a hidden version tag doing so.
    """
    text = prompt_text

    has_severity_definitions = bool(
        re.search(r"Kritisch:.*blockiert", text, re.DOTALL)
        and "Niedrig:" in text
    )
    has_sla_magnitude_example = bool(
        re.search(r"2\s*\*\s*\w+\s*=?\s*\d+", text)
        or "Faktor 2x" in text
    )
    has_output_schema = bool(
        "GENAU EINEM Satz" in text
        or "STRIKT einhalten" in text
    )

    return {
        "has_severity_definitions": has_severity_definitions,
        "has_sla_magnitude_example": has_sla_magnitude_example,
        "has_output_schema": has_output_schema,
    }
