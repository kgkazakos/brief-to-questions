"""Heuristic mapping from a research question to a suitable method.

This is intentionally opinionated but transparent. It maps the *shape* of a
question (what it is trying to learn) to a method that can credibly answer it.
The rationale string is part of the contract: a method without a reason is a
guess, and this tool's whole point is to make method choice defensible.
"""

from __future__ import annotations

from .models import QuestionType, ResearchMethod

# (method, rationale) keyed by the lexical intent of the question.
_INTENT_MAP: list[tuple[tuple[str, ...], ResearchMethod, str]] = [
    (
        ("how many", "what proportion", "what percentage", "how often",
         "how frequently", "prevalence", "rate of"),
        ResearchMethod.SURVEY,
        "Magnitude and frequency questions need a sample large enough to "
        "estimate proportions, which favours a survey over qualitative work.",
    ),
    (
        ("can users", "are users able", "complete the task", "find the",
         "where do users get stuck", "succeed in", "without help"),
        ResearchMethod.USABILITY_TEST,
        "Task-success and friction questions are best answered by watching "
        "people attempt the task, where behaviour is observed rather than reported.",
    ),
    (
        ("over time", "across days", "across weeks", "in their daily",
         "in context", "in the moment", "throughout"),
        ResearchMethod.DIARY_STUDY,
        "Behaviour and feeling that unfold over time are missed by a single "
        "session, so a longitudinal diary captures the lived pattern.",
    ),
    (
        ("in their environment", "at home", "at work", "on site",
         "real setting", "natural setting", "their workflow"),
        ResearchMethod.FIELD_STUDY,
        "Context shapes behaviour, so observing people in their own environment "
        "surfaces workarounds and constraints a lab would hide.",
    ),
    (
        ("organise", "organize", "categor", "group", "label", "navigation",
         "find content", "information architecture", "menu"),
        ResearchMethod.CARD_SORT,
        "Questions about how people group or expect to find things map cleanly "
        "to a card sort or tree test on the proposed structure.",
    ),
    (
        ("would they use", "appeal", "value proposition", "react to the concept",
         "interest in", "willing to", "concept", "early reaction"),
        ResearchMethod.CONCEPT_TEST,
        "Reactions to an idea that does not yet exist are best gathered with a "
        "concept test using lightweight stimulus, before build cost is sunk.",
    ),
    (
        ("does it increase", "does it improve", "causal", "impact of",
         "effect of", "moves the metric", "lift", "drives conversion"),
        ResearchMethod.AB_TEST,
        "A causal claim about a metric needs a controlled comparison; an A/B or "
        "multivariate test isolates the effect of the change.",
    ),
    (
        ("currently", "today", "right now", "existing behaviour",
         "what are users doing", "drop off", "funnel", "usage pattern"),
        ResearchMethod.ANALYTICS,
        "What is already happening in the product can be read from behavioural "
        "analytics before spending participant time.",
    ),
    (
        ("known about", "prior research", "literature", "evidence base",
         "what is established", "best practice"),
        ResearchMethod.LITERATURE_REVIEW,
        "If the field likely already has an answer, a secondary review is faster "
        "and cheaper than fresh primary research.",
    ),
    (
        ("why", "how do", "what motivates", "what prevents", "experience of",
         "mental model", "perceive", "make sense of", "reasons"),
        ResearchMethod.INTERVIEW,
        "Why-and-how questions about motivation and meaning need the depth and "
        "follow-up that only generative interviews provide.",
    ),
]

# Fallback by question type when no lexical cue matches.
_TYPE_FALLBACK: dict[QuestionType, tuple[ResearchMethod, str]] = {
    QuestionType.DESCRIPTIVE: (
        ResearchMethod.SURVEY,
        "A descriptive question about what or how many is most efficiently "
        "answered at scale with a survey.",
    ),
    QuestionType.EXPLORATORY: (
        ResearchMethod.INTERVIEW,
        "An exploratory question about motivation and meaning calls for the "
        "depth of generative interviews.",
    ),
    QuestionType.EVALUATIVE: (
        ResearchMethod.USABILITY_TEST,
        "An evaluative question about whether something works is best answered "
        "by observing people use it.",
    ),
    QuestionType.CAUSAL: (
        ResearchMethod.AB_TEST,
        "A causal question needs a controlled comparison to isolate the effect.",
    ),
}


def classify_question_type(question: str) -> QuestionType:
    """Infer the epistemic type of a question from its wording."""
    low = question.lower().strip()
    if low.startswith(("why", "how do", "how does", "what motivates", "what prevents")):
        return QuestionType.EXPLORATORY
    if any(c in low for c in ("can users", "are users able", "how well", "does it work", "complete the task")):
        return QuestionType.EVALUATIVE
    if any(c in low for c in ("does", "cause", "impact of", "effect of", "lead to", "result in")):
        return QuestionType.CAUSAL
    return QuestionType.DESCRIPTIVE


def map_method(question: str, qtype: QuestionType) -> tuple[ResearchMethod, str]:
    """Map a question to a method and return (method, rationale)."""
    low = question.lower()
    for cues, method, rationale in _INTENT_MAP:
        if any(cue in low for cue in cues):
            return method, rationale
    return _TYPE_FALLBACK[qtype]
