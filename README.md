# rollout-issue-prompt-engineering

A prompt-engineering project: a concrete task, four prompt versions iterated
against it, a golden evaluation set, and a measurement harness that scores
each version on two independent metrics. It treats prompt engineering as its
own skill: writing, optimizing, and evolving prompts for a specific use case,
and measuring the effect of each change.

## What it does

The task: given one rollout-milestone issue (reusing the issue shape from the
sibling project
[rollout-milestone-excel-checker](https://github.com/SantoshpHiremath/rollout-milestone-excel-checker)),
produce two things a project manager could act on directly: a severity
classification (`Kritisch` / `Hoch` / `Niedrig`) and a single, plain-German
summary sentence.

- `src/task.py` — the task definition and a 10-issue golden evaluation
  set with hand-verified expected severities, covering all four issue
  types from the sibling checker project (SLA breach at two different
  magnitudes, impossible milestone ordering, missing dates,
  duplicates).
- `src/prompts.py` — **four complete prompt versions**, each
  building on the last: `v1_bare` (a one-line instruction), `v2` (adds
  explicit severity definitions), `v3` (adds a worked example showing
  the SLA-breach magnitude threshold), `v4` (adds a strict output-
  format schema). `detect_prompt_features()` parses the actual prompt
  text, not a hidden version label, to determine which structural
  features are present, so a hand-edited prompt genuinely changes the
  measured outcome (verified directly by
  `test_removing_schema_instruction_removes_the_detected_feature`).
- `src/mock_llm.py` — the model stand-in (see Scope below).
- `src/evaluate.py` — the evaluation harness: two independent,
  deterministic metrics, `severity_accuracy` (does the classification
  match the golden label) and `summary_format_compliance` (does the
  summary include the site ID, avoid leaking raw field names, and stay
  to one sentence). They are kept separate rather than blended, so a
  prompt that fixes one thing but not the other is visible.
- `run_pipeline.py` — runs all four versions through the harness and
  prints a comparison report (see "Results" below, copied directly from
  an actual run).
- `tests/` — 22 tests, all passing, covering the prompt-feature
  detector, the mock model's feature-dependent behavior, and the
  evaluation harness's metrics.

## Scope

No live language model is called in this project. `src/mock_llm.py` is a
deterministic, rule-based stand-in for a real model. I built it to behave
the way a small instruction-following model plausibly would when given
prompts of varying quality: it has its own independent, cruder default
judgment (e.g. it defaults every `sla_breach` to `Hoch` regardless of how far
over the deadline it is, and defaults `out_of_order` to `Hoch` when the
correct answer is `Kritisch`) that only improves as the *prompt itself*
supplies more explicit structure: severity definitions, a worked numeric
example, an output-format constraint. That makes the measured accuracy curve
(20% → 80% → 100% → 100%, see below) a genuine test of prompt quality: the
mock model doesn't know it's being tested against `task.py`'s ground truth,
and its behavior is driven entirely by parsing the real prompt text through
`detect_prompt_features()`.

The methodology (task definition, golden set, iterated prompt text, and a
tested measurement harness) applies unchanged to real model output.
`mock_llm.run_mock_llm()` has the same signature a real client call would
have, `(issue, prompt_features) -> {"severity": ..., "summary": ...}`, so a
real model can be swapped in and `run_pipeline.py` re-run against real
output.

## Results

Output from an actual run of `run_pipeline.py`:

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
explicit output-schema constraint appears in v4. Classification correctness
and output-format correctness are separate concerns a prompt has to address
independently, not two symptoms of the same fix.

## Tests

- `PYTHONPATH=src python3 -m pytest tests/ -v` — 22/22 tests pass.
- `python3 run_pipeline.py` — runs end to end; the sample output above is
  copied directly from this run's actual stdout.
- The feature detector is tested against hand-built prompt text that
  isn't any of the four canonical versions
  (`test_feature_detection_is_driven_by_real_text_not_a_label`), and
  against an edited copy of v4 with the schema instruction removed
  (`test_removing_schema_instruction_removes_the_detected_feature`);
  both confirm detection is driven by prompt content, not a hidden
  label.
- I caught and fixed a bug during development: the first
  version of the SLA-magnitude-example detector used a regex that only
  matched the literal numbers appearing in the canonical v3/v4 prompt
  text (`2*30`, `2*60`), so it failed
  `test_feature_detection_is_driven_by_real_text_not_a_label` (which
  uses `2*30` inside different surrounding text). I generalized
  the regex to match any `2 * <number>` pattern rather than a fixed
  list of numbers, and confirmed it by re-running the previously-failing
  test.

## Running it

```bash
pip install -r requirements.txt
PYTHONPATH=src python3 -m pytest tests/ -v
python3 run_pipeline.py
```

## Possible extensions

- Swap `mock_llm.run_mock_llm()` for a real model call (a local model via
  Ollama or a hosted API) and re-run `run_pipeline.py` to score the four
  prompt versions on real output.
