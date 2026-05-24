"""Rule-based research question generation.

Each brief element is turned into one or more candidate research questions using
templates keyed by element kind. The templates are written to produce questions
that are answerable and non-leading by construction; the critic still checks
them afterwards as a safety net. Priority is seeded from element kind (decisions
and untested assumptions matter most) and can be overridden by the LLM layer.
"""

from __future__ import annotations

import re

from .critic import critique
from .methods import classify_question_type, map_method
from .models import BriefElement, ElementKind, ResearchQuestion

# Default decision-impact priority by element kind (1 = highest).
_PRIORITY: dict[ElementKind, int] = {
    ElementKind.DECISION: 1,
    ElementKind.ASSUMPTION: 2,
    ElementKind.OPEN_QUESTION: 2,
    ElementKind.GOAL: 3,
    ElementKind.METRIC: 3,
    ElementKind.USER: 4,
    ElementKind.CONSTRAINT: 4,
}


def _clean_subject(text: str) -> str:
    """Strip leading cue words so the element reads as a noun-ish subject."""
    s = text.strip().rstrip(".!?")
    s = re.sub(
        r"^(we (want to|aim to|need to|assume|believe|think|expect|will)|the (goal|objective|aim) is( to)?|our goal is to|should we|whether to)\s+",
        "",
        s,
        flags=re.IGNORECASE,
    )
    return s.strip()


def _questions_for(element: BriefElement) -> list[str]:
    """Produce candidate question strings for one element."""
    subject = _clean_subject(element.text)
    kind = element.kind

    # A subject that collapsed to almost nothing yields garbage questions.
    if kind != ElementKind.OPEN_QUESTION and len(subject.split()) < 2:
        return []

    if kind == ElementKind.ASSUMPTION:
        return [
            f"To what extent does the evidence support the belief that {subject.lower()}?",
            f"How do users actually behave in the situation where we assume {subject.lower()}?",
        ]
    if kind == ElementKind.DECISION:
        return [
            f"What would users need to be true for us to confidently {subject.lower()}?",
            f"How do the options behind '{subject}' compare from the user's point of view?",
        ]
    if kind == ElementKind.OPEN_QUESTION:
        # Already a question — keep it, but make it researchable.
        base = element.text.strip()
        if not base.endswith("?"):
            base += "?"
        return [base]
    if kind == ElementKind.GOAL:
        return [
            f"What currently stops users from being able to {subject.lower()}?",
            f"How do users approach {subject.lower()} today, and where does it break down?",
        ]
    if kind == ElementKind.METRIC:
        return [
            f"What user behaviours move the metric described by '{subject}'?",
            f"How do users interpret the experience that '{subject}' is meant to capture?",
        ]
    if kind == ElementKind.USER:
        return [
            f"What distinguishes the needs of {subject.lower()} from other segments?",
            f"How do {subject.lower()} currently solve the problem this product addresses?",
        ]
    if kind == ElementKind.CONSTRAINT:
        return [
            f"How does the constraint '{subject}' affect what users can realistically do?",
        ]
    return [f"How do users experience '{subject}'?"]


def generate_questions(elements: list[BriefElement]) -> list[ResearchQuestion]:
    """Generate, de-duplicate, method-map, critique and sort research questions."""
    seen: set[str] = set()
    questions: list[ResearchQuestion] = []

    for element in elements:
        # Skip the weakest goal guesses to avoid drowning the output in noise.
        if element.kind == ElementKind.GOAL and element.confidence < 0.4:
            continue
        for q_text in _questions_for(element):
            key = q_text.lower()
            if key in seen:
                continue
            seen.add(key)
            qtype = classify_question_type(q_text)
            method, rationale = map_method(q_text, qtype)
            questions.append(
                ResearchQuestion(
                    text=q_text,
                    question_type=qtype,
                    method=method,
                    method_rationale=rationale,
                    informs_decision=_informs(element),
                    priority=_PRIORITY.get(element.kind, 3),
                    flags=critique(q_text),
                    source=element.text,
                )
            )

    # Stable sort by priority (1 first), preserving discovery order within a tier.
    questions.sort(key=lambda q: q.priority)
    return questions


def _informs(element: BriefElement) -> str:
    if element.kind == ElementKind.DECISION:
        return f"The decision: {_clean_subject(element.text)}"
    if element.kind == ElementKind.ASSUMPTION:
        return f"Whether to act on the assumption that {_clean_subject(element.text).lower()}"
    if element.kind == ElementKind.GOAL:
        return f"How to reach the goal: {_clean_subject(element.text).lower()}"
    if element.kind == ElementKind.METRIC:
        return f"How to move: {_clean_subject(element.text)}"
    return "General product direction"
