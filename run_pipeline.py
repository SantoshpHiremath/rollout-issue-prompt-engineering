"""
End-to-end demo: run all four prompt versions through the evaluation
harness against the golden issue set, and print a comparison report.
"""

import sys
sys.path.insert(0, "src")

from prompts import PROMPT_VERSIONS
from evaluate import compare_prompt_versions
from task import GOLDEN_ISSUES


def main():
    print("=" * 70)
    print("PROMPT-ENGINEERING ITERATION: ROLLOUT-ISSUE KLASSIFIZIERUNG")
    print("=" * 70)
    print(f"\nGolden-Set-Größe: {len(GOLDEN_ISSUES)} Issues")

    results = compare_prompt_versions(PROMPT_VERSIONS)

    print(f"\n{'Version':<24}{'Features erkannt':<50}{'Severity-Genauigkeit':<24}{'Format-Konformität'}")
    print("-" * 118)
    for name, r in results.items():
        features_str = ", ".join(k.replace("has_", "") for k, v in r["detected_features"].items() if v) or "keine"
        acc_str = f"{r['severity_accuracy']:.0%}"
        fmt_str = f"{r['summary_format_compliance']:.0%}"
        print(f"{name:<24}{features_str:<50}{acc_str:<24}{fmt_str}")

    print("\n" + "=" * 70)
    print("Detail: v1 (bare) vs. v4 (mit Definitionen + Beispiel + Schema)")
    print("=" * 70)
    v1 = results["v1_bare"]
    v4 = results["v4_with_output_schema"]
    for r1, r4 in zip(v1["results"], v4["results"]):
        if r1["site_id"] != r4["site_id"]:
            continue
        marker = "  " if r1["severity_correct"] == r4["severity_correct"] else ">>"
        print(f"{marker} {r1['site_id']} ({r1['issue_type']}): "
              f"erwartet={r1['expected_severity']} | "
              f"v1={r1['predicted_severity']}({'OK' if r1['severity_correct'] else 'FALSCH'}) | "
              f"v4={r4['predicted_severity']}({'OK' if r4['severity_correct'] else 'FALSCH'})")

    print("\n" + "=" * 70)
    print("Hinweis: Kein echtes LLM wurde aufgerufen (siehe README für die")
    print("vollständige Offenlegung) -- das Mock-Modell simuliert plausibles,")
    print("unvollkommenes Kleinmodell-Verhalten, das sich mit besser")
    print("strukturierten Prompts nachweislich verbessert, exakt wie hier")
    print("gemessen.")
    print("=" * 70)


if __name__ == "__main__":
    main()
