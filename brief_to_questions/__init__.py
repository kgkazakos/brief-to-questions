"""brief-to-questions: turn a PM brief or PRD into crisp, answerable,
methodologically sound research questions.

Part of the CPR Orbital Series by Kostas Kazakos.
"""

from __future__ import annotations

from .extractor import coverage_gaps, extract_elements
from .generator import generate_questions
from .models import (
    BriefAnalysis,
    BriefElement,
    ElementKind,
    QualityFlag,
    QuestionType,
    ResearchMethod,
    ResearchQuestion,
    Severity,
)
from .pipeline import analyse

__version__ = "0.1.0"

__all__ = [
    "analyse",
    "extract_elements",
    "generate_questions",
    "coverage_gaps",
    "BriefAnalysis",
    "BriefElement",
    "ResearchQuestion",
    "QualityFlag",
    "ElementKind",
    "QuestionType",
    "ResearchMethod",
    "Severity",
    "__version__",
]
