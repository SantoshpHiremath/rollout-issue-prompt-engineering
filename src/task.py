"""
The concrete task this project iterates a prompt against: given one
rollout-milestone issue (reusing the real issue shape from the sibling
project rollout-milestone-excel-checker), produce two things a project
manager could act on directly:

  1. severity: one of {"Kritisch", "Hoch", "Niedrig"}
  2. summary: a single, plain-German sentence describing the issue

The task is an AI-supported workflow for processing and evaluating
check and project information: an LLM turning a raw checker-output row
into an actionable classification + summary, in support of analyzing and
reporting on rollout figures.

Ground-truth severity rules (used only to build the golden evaluation
set and to grade a mock model's output -- NOT given to the model as
part of the prompt, since the whole point is testing whether prompt
wording alone gets the model to infer the right judgment):
  - "sla_breach" with gap_days > 2x max_allowed_days -> Kritisch
  - "sla_breach" with gap_days <= 2x max_allowed_days -> Hoch
  - "out_of_order" -> Kritisch (a logically impossible date order
    usually indicates a data-entry error that needs correction before
    anything downstream can be trusted)
  - "missing_date" -> Hoch
  - "duplicate" -> Niedrig (annoying but not urgent -- doesn't block
    the rollout, just needs deduplication)
"""

GOLDEN_ISSUES = [
    {
        "site_id": "SITE-20012",
        "issue": "sla_breach",
        "milestone": "Inbetriebnahme",
        "prerequisite": "Bau",
        "gap_days": 95,
        "max_allowed_days": 30,
        "expected_severity": "Kritisch",  # 95 > 2*30
    },
    {
        "site_id": "SITE-20044",
        "issue": "sla_breach",
        "milestone": "Genehmigung",
        "prerequisite": "Standortakquise",
        "gap_days": 70,
        "max_allowed_days": 60,
        "expected_severity": "Hoch",  # 70 <= 2*60
    },
    {
        "site_id": "SITE-20101",
        "issue": "out_of_order",
        "milestone": "Bau",
        "prerequisite": "Genehmigung",
        "milestone_date": "2025-03-01",
        "prerequisite_date": "2025-03-10",
        "expected_severity": "Kritisch",
    },
    {
        "site_id": "SITE-20205",
        "issue": "missing_date",
        "milestone": "Bau",
        "expected_severity": "Hoch",
    },
    {
        "site_id": "SITE-20309",
        "issue": "duplicate",
        "occurrences": 2,
        "expected_severity": "Niedrig",
    },
    {
        "site_id": "SITE-20410",
        "issue": "sla_breach",
        "milestone": "Bau",
        "prerequisite": "Genehmigung",
        "gap_days": 200,
        "max_allowed_days": 90,
        "expected_severity": "Kritisch",  # 200 > 2*90
    },
    {
        "site_id": "SITE-20512",
        "issue": "sla_breach",
        "milestone": "Inbetriebnahme",
        "prerequisite": "Bau",
        "gap_days": 32,
        "max_allowed_days": 30,
        "expected_severity": "Hoch",  # barely over, 32 <= 2*30
    },
    {
        "site_id": "SITE-20633",
        "issue": "missing_date",
        "milestone": "Inbetriebnahme",
        "expected_severity": "Hoch",
    },
    {
        "site_id": "SITE-20744",
        "issue": "duplicate",
        "occurrences": 3,
        "expected_severity": "Niedrig",
    },
    {
        "site_id": "SITE-20855",
        "issue": "out_of_order",
        "milestone": "Inbetriebnahme",
        "prerequisite": "Bau",
        "milestone_date": "2025-06-01",
        "prerequisite_date": "2025-06-15",
        "expected_severity": "Kritisch",
    },
]
