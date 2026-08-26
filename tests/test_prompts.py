import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prompts import PROMPT_VERSIONS, detect_prompt_features, PROMPT_V1, PROMPT_V4


def test_all_four_versions_exist():
    assert len(PROMPT_VERSIONS) == 4
    assert set(PROMPT_VERSIONS.keys()) == {
        "v1_bare", "v2_with_definitions", "v3_with_worked_example", "v4_with_output_schema",
    }


def test_v1_has_no_detected_features():
    features = detect_prompt_features(PROMPT_V1)
    assert not any(features.values())


def test_v4_has_all_detected_features():
    features = detect_prompt_features(PROMPT_V4)
    assert all(features.values())


def test_feature_detection_is_driven_by_real_text_not_a_label():
    """
    detect_prompt_features must read the actual prompt string, not key
    off a version name -- proven by feeding it a hand-built string that
    isn't any of the four canonical versions and confirming detection
    still works correctly.
    """
    custom_prompt = (
        "Kritisch: blockiert den Rollout.\n"
        "Niedrig: stört nicht.\n"
        "Beispiel: gap_days=95, max_allowed_days=30 -> 95 > 2*30 -> Kritisch\n"
    )
    features = detect_prompt_features(custom_prompt)
    assert features["has_severity_definitions"] is True
    assert features["has_sla_magnitude_example"] is True
    assert features["has_output_schema"] is False


def test_removing_schema_instruction_removes_the_detected_feature():
    """
    A regression-style test: editing v4's text to remove the schema
    instruction should flip has_output_schema back to False -- proving
    the detector responds to content, not to which named version was
    passed in.
    """
    edited = PROMPT_V4.replace("GENAU EINEM Satz", "einem Satz").replace("STRIKT einhalten", "einhalten")
    features = detect_prompt_features(edited)
    assert features["has_output_schema"] is False


def test_each_prompt_version_contains_the_issue_placeholder():
    for name, text in PROMPT_VERSIONS.items():
        assert "{issue}" in text, f"{name} is missing the {{issue}} placeholder"
