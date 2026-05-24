"""Quality checks for individual research questions.

These are the checks a careful researcher runs in their head when reviewing a
discussion guide: is this leading, is it double-barrelled, is it vague, is it
actually answerable. They run on the final question text regardless of whether
it was written by the rule-based generator or refined by the LLM layer.
"""

from __future__ import annotations

import re

from .models import QualityFlag, ResearchQuestion, Severity

_LEADING_TERMS = (
    "obviously", "clearly", "surely", "wouldn't you", "don't you", "isn't it",
    "amazing", "great", "love", "hate", "best", "worst", "easy", "simple",
    "frustrating", "annoying",
)

_VAGUE_TERMS = (
    "stuff", "things", "various", "generally", "in general", "overall",
    "user experience", "engagement", "satisfaction", "needs",
)

_ABSOLUTE_TERMS = ("always", "never", "everyone", "no one", "all users", "every user")


def _flag_leading(text: str) -> QualityFlag | None:
    low = text.lower()
    hits = [t for t in _LEADING_TERMS if t in low]
    if hits:
        return QualityFlag(
            code="leading",
            message=f"Loaded or leading wording ({', '.join(sorted(set(hits)))}) may bias responses.",
            severity=Severity.WARNING,
        )
    return None


def _flag_double_barrelled(text: str) -> QualityFlag | None:
    # Two distinct asks joined by 'and'/'or' inside one question.
    core = text.rstrip("?").strip()
    if re.search(r"\b(and|or)\b", core.lower()) and core.lower().count(" and ") + core.lower().count(" or ") >= 1:
        # Only flag when both sides look like separate asks (heuristic: a verb on each side).
        parts = re.split(r"\b(?:and|or)\b", core.lower())
        verbish = sum(1 for p in parts if re.search(r"\b(do|does|use|want|feel|think|complete|find|need)\b", p))
        if verbish >= 2:
            return QualityFlag(
                code="double_barrelled",
                message="Question bundles two asks — split it so each can be answered cleanly.",
                severity=Severity.WARNING,
            )
    return None


def _flag_vague(text: str) -> QualityFlag | None:
    low = text.lower()
    hits = [t for t in _VAGUE_TERMS if t in low]
    if hits:
        return QualityFlag(
            code="vague",
            message=f"Abstract term(s) ({', '.join(sorted(set(hits)))}) need a concrete, observable definition.",
            severity=Severity.INFO,
        )
    return None


def _flag_absolute(text: str) -> QualityFlag | None:
    low = text.lower()
    hits = [t for t in _ABSOLUTE_TERMS if t in low]
    if hits:
        return QualityFlag(
            code="absolute",
            message=f"Absolute framing ({', '.join(sorted(set(hits)))}) sets an unanswerable bar — soften it.",
            severity=Severity.INFO,
        )
    return None


def _flag_closed(text: str) -> QualityFlag | None:
    # A bare yes/no question in a generative context yields thin data.
    if re.match(r"^\s*(do|does|did|is|are|was|were|will|would|can|could|should|have|has)\b", text.lower()):
        if "?" in text and not re.search(r"\b(why|how|what|which|to what extent)\b", text.lower()):
            return QualityFlag(
                code="closed",
                message="Closed yes/no framing — consider 'how' or 'to what extent' for richer answers.",
                severity=Severity.INFO,
            )
    return None


def _flag_unanswerable(text: str) -> QualityFlag | None:
    low = text.lower()
    if any(t in low for t in ("ideal", "perfect", "would you want in future", "in five years", "dream")):
        return QualityFlag(
            code="speculative",
            message="Speculative or aspirational framing invites unreliable self-report.",
            severity=Severity.WARNING,
        )
    return None


_CHECKS = (
    _flag_leading,
    _flag_double_barrelled,
    _flag_vague,
    _flag_absolute,
    _flag_closed,
    _flag_unanswerable,
)


def critique(text: str) -> list[QualityFlag]:
    """Run all quality checks against a question string."""
    flags: list[QualityFlag] = []
    for check in _CHECKS:
        flag = check(text)
        if flag is not None:
            flags.append(flag)
    return flags


def critique_question(question: ResearchQuestion) -> ResearchQuestion:
    """Attach quality flags to a question in place and return it."""
    question.flags = critique(question.text)
    return question
