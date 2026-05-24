"""Core data models for brief-to-questions.

These dataclasses and enums form the shared vocabulary between the rule-based
core (extractor, generator, critic, methods) and the optional LLM enrichment
layer. Everything here is plain-Python and has zero third-party dependencies so
that the core pipeline runs fully offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ElementKind(str, Enum):
    """A unit of meaning extracted from a PM brief or PRD."""

    GOAL = "goal"
    ASSUMPTION = "assumption"
    DECISION = "decision"
    USER = "user"
    METRIC = "metric"
    CONSTRAINT = "constraint"
    OPEN_QUESTION = "open_question"


class QuestionType(str, Enum):
    """The epistemic shape of a research question."""

    DESCRIPTIVE = "descriptive"  # what / who / when / how many
    EXPLORATORY = "exploratory"  # why / how do people
    EVALUATIVE = "evaluative"  # can users / how well does X work
    CAUSAL = "causal"  # does X change Y


class ResearchMethod(str, Enum):
    """A method capable of answering a question. Not exhaustive, but covers the
    bread-and-butter of applied product research."""

    INTERVIEW = "Generative interviews"
    SURVEY = "Survey"
    USABILITY_TEST = "Usability test"
    DIARY_STUDY = "Diary study"
    FIELD_STUDY = "Contextual / field study"
    CARD_SORT = "Card sort / tree test"
    CONCEPT_TEST = "Concept test"
    AB_TEST = "A/B or multivariate test"
    ANALYTICS = "Behavioural analytics review"
    LITERATURE_REVIEW = "Secondary / literature review"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BriefElement:
    """A single extracted signal from the brief."""

    kind: ElementKind
    text: str
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {"kind": self.kind.value, "text": self.text, "confidence": round(self.confidence, 3)}


@dataclass
class QualityFlag:
    """A methodological concern attached to a question."""

    code: str
    message: str
    severity: Severity

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "severity": self.severity.value}


@dataclass
class ResearchQuestion:
    """A crisp, answerable, method-mapped research question."""

    text: str
    question_type: QuestionType
    method: ResearchMethod
    method_rationale: str
    informs_decision: str
    priority: int = 3  # 1 = highest decision impact, 5 = lowest
    flags: list[QualityFlag] = field(default_factory=list)
    source: str = ""
    llm_enriched: bool = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "question_type": self.question_type.value,
            "method": self.method.value,
            "method_rationale": self.method_rationale,
            "informs_decision": self.informs_decision,
            "priority": self.priority,
            "flags": [f.to_dict() for f in self.flags],
            "source": self.source,
            "llm_enriched": self.llm_enriched,
        }


@dataclass
class BriefAnalysis:
    """The full output of the pipeline."""

    elements: list[BriefElement]
    questions: list[ResearchQuestion]
    summary: str
    coverage_notes: list[str] = field(default_factory=list)
    llm_backend: str | None = None

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "llm_backend": self.llm_backend,
            "elements": [e.to_dict() for e in self.elements],
            "questions": [q.to_dict() for q in self.questions],
            "coverage_notes": self.coverage_notes,
        }
