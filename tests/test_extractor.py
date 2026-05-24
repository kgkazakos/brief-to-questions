from pathlib import Path

from brief_to_questions.extractor import coverage_gaps, extract_elements
from brief_to_questions.models import ElementKind

FIXTURE = Path(__file__).parent / "fixtures" / "sample_brief.md"


def test_extracts_elements_from_fixture():
    elements = extract_elements(FIXTURE.read_text())
    assert len(elements) >= 6
    kinds = {e.kind for e in elements}
    assert ElementKind.ASSUMPTION in kinds
    assert ElementKind.DECISION in kinds
    assert ElementKind.OPEN_QUESTION in kinds


def test_assumption_detected():
    elements = extract_elements("We assume users will trust the suggestions.")
    assert elements[0].kind == ElementKind.ASSUMPTION


def test_decision_detected():
    elements = extract_elements("Should we ship the full feature or a smaller cut?")
    # Trailing '?' makes this an open question by rule; ensure decision cue still classifies non-question form.
    el = extract_elements("We need to decide whether to ship the full feature.")
    assert el[0].kind == ElementKind.DECISION
    assert elements[0].kind == ElementKind.OPEN_QUESTION


def test_metric_detected():
    elements = extract_elements("Success metric: reduce handle time by 20%.")
    assert elements[0].kind == ElementKind.METRIC


def test_question_mark_becomes_open_question():
    elements = extract_elements("Why do users abandon onboarding?")
    assert elements[0].kind == ElementKind.OPEN_QUESTION
    assert elements[0].confidence >= 0.8


def test_dedup_collapses_repeats():
    elements = extract_elements("We want to grow retention.\nWe want to grow retention.")
    assert len(elements) == 1


def test_coverage_gaps_flag_missing_kinds():
    notes = coverage_gaps(extract_elements("We want to grow retention."))
    # No user, metric, decision, or assumption -> several notes.
    assert len(notes) >= 3
