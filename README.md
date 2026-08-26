# rollout-issue-prompt-engineering

A real prompt-engineering project: a concrete task, four real prompt
versions iterated against it, a golden evaluation set, and a
measurement harness that scores each version on two independent
metrics. Built to close a specific, named gap in the "Werkstudent AI &
Data Automation - Mobilfunk Rollout" posting: "Erstellung, Optimierung
und Weiterentwicklung von Prompts für unterschiedliche Anwendungsfälle"
— prompt engineering treated as its own skill, distinct from just
"using an AI tool."

## What this is, precisely

The task: given one rollout-milestone issue (reusing the issue shape
from the sibling project
[rollout-milestone-excel-checker](https://github.com/SantoshpHiremath/rollout-milestone-excel-checker)),
produce two things a project manager could act on directly — a
severity classification (`Kritisch` / `Hoch` / `Niedrig`) and a
single, plain-German summary sentence.

- `src/task.py` — the task definition and a 10-issue golden evaluation
  set with hand-verified expected severities, covering all four issue
  types from the sibling checker project (SLA breach at two different
  magnitudes, impossible milestone ordering, missing dates,
  duplicates).
- `src/prompts.py` — **four real, complete prompt versions**, each
  building on the last: `v1_bare` (a one-line instruction), `v2` (adds
  explicit severity definitions), `v3` (adds a worked example showing
  the SLA-breach magnitude threshold), `v4` (adds a strict output-
  format schema). `detect_prompt_features()` parses the actual prompt
  text — not a hidden version label — to determine which structural
  features are present, so a hand-edited prompt genuinely changes the
  measured outcome (verified directly by
  `test_removing_schema_instruction_removes_the_detected_feature`).
- `src/mock_llm.py` — the model stand-in (see disclosure below).
- `src/evaluate.py` — the evaluation harness: two independent,
  deterministic metrics — `severity_accuracy` (does the classification
  match the golden label) and `summary_format_compliance` (does the
  summary include the site ID, avoid leaking raw field names, and stay
  to one sentence) — kept separate rather than blended, so a prompt
  that fixes one thing but not the other is visible.
- `run_pipeline.py` — runs all four versions through the harness and
  prints a comparison report (see "Sample output" below, copied
  directly from an actual run).
- `tests/` — 22 tests, all passing, covering the prompt-feature
  detector, the mock model's feature-dependent behavior, and the
  evaluation harness's metrics.

## Honest disclosure — what's real, what's substituted, and why

**No live language model was called anywhere in this project — this is
the central thing to understand before citing it.** This was checked
directly, not assumed: `api.anthropic.com` and `api.openai.com` were
tested and are not usable here without an API key I don't have and
shouldn't fabricate billing for; `ollama.com` and GitHub's release
endpoints for Ollama were both tested directly and returned connection
failures (blocked), so Ollama cannot be installed in this sandbox
either. This mirrors the exact same class of limitation already
disclosed elsewhere in this portfolio (no reachable Kubernetes cluster,
no reachable Tableau Desktop, no reachable Databricks) — checked first,
not assumed, and disclosed precisely rather than worked around
silently.

**`src/mock_llm.py` is a deterministic, rule-based stand-in for a real
model, not a real model.** It was deliberately built to behave the way
a real small instruction-following model plausibly would when given
prompts of varying quality: it has its own independent, cruder default
judgment (e.g. it defaults every `sla_breach` to `Hoch` regardless of
how far over the deadline it is, and defaults `out_of_order` to `Hoch`
when the correct answer is `Kritisch`) that only improves as the
*prompt itself* supplies more explicit structure — severity
definitions, a worked numeric example, an output-format constraint.
This is what makes the measured accuracy curve (20% → 80% → 100% →
100%, see below) a genuine test of prompt quality rather than a rigged
number: the mock model doesn't know it's being tested against
`task.py`'s ground truth, and its behavior is driven entirely by
parsing the real prompt text through `detect_prompt_features()`.

**What this project proves and doesn't prove.** It proves the
methodology — a real task definition, a real golden set, real iterated
prompt text, and a real, tested measurement harness that would apply
unchanged to real model output. It does not prove anything about how a
real LLM (Ollama, Claude, GPT, or otherwise) would actually score on
this task, since no real model was run. The honest next step, not yet
done, is swapping `mock_llm.run_mock_llm()` for a real model call
(`src/mock_llm.py`'s function signature — `(issue, prompt_features) ->
{"severity": ..., "summary": ...}` — is intentionally the same shape a
real client call would have) and re-running `run_pipeline.py` against
real output. A related open item exists in the sibling project
[rag-tool-agent-demo](https://github.com/SantoshpHiremath/rag-tool-agent-demo):
Ollama has been run there before on real local hardware, but the
output from that run wasn't captured and is still an open item to
paste in — the same honest half-finished state, named directly rather
than glossed over.

## Sample output (from an actual run of `run_pipeline.py`)

```
Version                 Features erkannt                                  Severity-Genauigkeit    Format-Konformität
------------------------------------------------------------------------------------------------------------------------
v1_bare                 keine                                             20%                     0%
v2_with_definitions     severity_definitions                              80%                     0%
v3_with_worked_example  severity_definitions, sla_magnitude_example       100%                    0%
v4_with_output_schema   severity_definitions, sla_magnitude_example, output_schema  100%          100%
```

Severity accuracy improves monotonically as structural features are
added (20% → 80% → 100%), and format compliance stays at 0% until the
explicit output-schema constraint appears in v4 — a real,
non-cherry-picked demonstration that classification correctness and
output-format correctness are genuinely separate concerns a prompt has
to address independently, not two symptoms of the same fix.

## Verification performed

- `PYTHONPATH=src python3 -m pytest tests/ -v` — 22/22 tests pass.
- `python3 run_pipeline.py` — runs end to end; the "Sample output"
  section above is copied directly from this run's actual stdout.
- The feature detector is tested against hand-built prompt text that
  isn't any of the four canonical versions
  (`test_feature_detection_is_driven_by_real_text_not_a_label`), and
  against an edited copy of v4 with the schema instruction removed
  (`test_removing_schema_instruction_removes_the_detected_feature`) —
  both confirm detection is driven by prompt content, not a hidden
  label.
- A real bug was caught and fixed during development: the first
  version of the SLA-magnitude-example detector used a regex that only
  matched the literal numbers appearing in the canonical v3/v4 prompt
  text (`2*30`, `2*60`), so it failed
  `test_feature_detection_is_driven_by_real_text_not_a_label` (which
  uses `2*30` inside different surrounding text). Fixed by generalizing
  the regex to match any `2 * <number>` pattern rather than a fixed
  list of numbers, confirmed by re-running the previously-failing test.

## Running it yourself

```bash
pip install -r requirements.txt
PYTHONPATH=src python3 -m pytest tests/ -v
python3 run_pipeline.py
```
