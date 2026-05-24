from brief_to_questions.extractor import extract_elements
from brief_to_questions.generator import generate_questions
from brief_to_questions.models import BriefElement, ElementKind


def test_generates_questions():
    elements = extract_elements(
        "We assume users trust suggestions.\nShould we ship full replies or short ones?"
    )
    questions = generate_questions(elements)
    assert len(questions) >= 2
    assert all(q.text for q in questions)


def test_priority_sorted_decision_first():
    elements = [
        BriefElement(kind=ElementKind.GOAL, text="We want to grow retention", confidence=0.7),
        BriefElement(kind=ElementKind.DECISION, text="We need to decide whether to cut the checklist", confidence=0.7),
    ]
    questions = generate_questions(elements)
    assert questions[0].priority == 1


def test_each_question_has_method_and_rationale():
    elements = extract_elements("Why do users abandon onboarding?")
    questions = generate_questions(elements)
    for q in questions:
        assert q.method is not None
        assert q.method_rationale


def test_low_confidence_goal_skipped():
    elements = [BriefElement(kind=ElementKind.GOAL, text="random line", confidence=0.35)]
    assert generate_questions(elements) == []


def test_questions_are_deduped():
    elements = [
        BriefElement(kind=ElementKind.OPEN_QUESTION, text="Why do users churn?", confidence=0.9),
        BriefElement(kind=ElementKind.OPEN_QUESTION, text="Why do users churn?", confidence=0.9),
    ]
    questions = generate_questions(elements)
    assert len(questions) == 1
