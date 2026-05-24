"""Rule-based extraction of structured elements from a PM brief or PRD.

The extractor is deliberately simple and explainable. It splits the brief into
candidate statements and classifies each one using lexical cues. It will never
be as nuanced as the LLM layer, but it always runs, it is fully deterministic,
and it gives the generator something concrete to work with offline.
"""

from __future__ import annotations

import re

from .models import BriefElement, ElementKind

# Lexical cues per element kind. Order matters: the first kind whose cue matches
# wins, so more specific kinds are listed before broader ones.
_CUES: list[tuple[ElementKind, tuple[str, ...]]] = [
    (
        ElementKind.OPEN_QUESTION,
        ("we don't know", "we do not know", "unclear", "unsure", "open question",
         "tbd", "to be determined", "need to understand", "not sure whether"),
    ),
    (
        ElementKind.DECISION,
        ("decide", "decision", "we will choose", "should we", "go/no-go",
         "whether to", "trade-off", "tradeoff", "prioritise", "prioritize"),
    ),
    (
        ElementKind.ASSUMPTION,
        ("we assume", "we believe", "we think", "we expect", "presumably",
         "hypothesis", "we hypothesise", "we hypothesize", "likely that",
         "users probably", "should want"),
    ),
    (
        ElementKind.METRIC,
        ("kpi", "north star", "success metric", "success is", "measured by",
         "conversion", "retention", "activation", "nps", "csat", "%",
         "increase", "reduce", "by 10", "by 20", "by 30", "uplift", "target of"),
    ),
    (
        ElementKind.USER,
        ("target user", "persona", "segment", "audience", "our users",
         "customers", "power users", "new users", "admins", "smb", "enterprise"),
    ),
    (
        ElementKind.CONSTRAINT,
        ("constraint", "deadline", "by q1", "by q2", "by q3", "by q4",
         "limited", "we cannot", "must not", "out of scope", "budget",
         "engineering capacity", "compliance", "regulatory"),
    ),
    (
        ElementKind.GOAL,
        ("goal", "objective", "we want to", "we aim to", "the aim is",
         "in order to", "so that", "drive", "improve", "grow", "enable",
         "we need to", "help users"),
    ),
]

_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.*)$|^\s*[-*]\s+|^\s*\d+[.)]\s+")
_BULLET_RE = re.compile(r"^\s*([-*•]|\d+[.)])\s+")

# Standalone section labels (often markdown headers) that carry no content of
# their own and should not become elements or questions.
_SECTION_LABELS = {
    "goal", "goals", "objective", "objectives", "target user", "target users",
    "users", "user", "audience", "assumption", "assumptions", "success metric",
    "success metrics", "metric", "metrics", "kpi", "kpis", "decision", "decisions",
    "constraint", "constraints", "open question", "open questions", "background",
    "context", "overview", "summary", "scope", "problem", "brief",
}


def _is_section_label(line: str) -> bool:
    bare = line.rstrip(":").strip().lower()
    return bare in _SECTION_LABELS


def _split_statements(text: str) -> list[str]:
    """Break the brief into candidate statements: bullets, headers, sentences."""
    statements: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip markdown header / bullet markers but keep the content.
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = _BULLET_RE.sub("", line)
        line = line.strip("•- *\t")
        if not line or _is_section_label(line):
            continue
        # Drop a leading "Label:" prefix (e.g. "Decision: ship X" -> "ship X").
        prefix_match = re.match(r"^([A-Za-z][A-Za-z /]{1,24}):\s+(.*)$", line)
        if prefix_match and _is_section_label(prefix_match.group(1)):
            line = prefix_match.group(2).strip()
        # A bullet line is usually one statement; a prose line may hold several
        # sentences, so split on sentence terminators.
        for chunk in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", line):
            chunk = chunk.strip()
            if len(chunk) >= 8 and len(chunk.split()) >= 2:
                statements.append(chunk)
    return statements


def _classify(statement: str) -> tuple[ElementKind, float]:
    """Classify a statement by lexical cue. Returns (kind, confidence)."""
    low = statement.lower()
    if statement.rstrip().endswith("?"):
        return ElementKind.OPEN_QUESTION, 0.9
    for kind, cues in _CUES:
        for cue in cues:
            if cue in low:
                return kind, 0.7
    # Default: treat a declarative statement as a goal with low confidence.
    return ElementKind.GOAL, 0.35


def extract_elements(brief: str) -> list[BriefElement]:
    """Extract structured elements from raw brief text.

    Duplicate statements (case-insensitive) are collapsed. Confidence reflects
    how strong the lexical signal was, not ground truth.
    """
    seen: set[str] = set()
    elements: list[BriefElement] = []
    for statement in _split_statements(brief):
        key = statement.lower()
        if key in seen:
            continue
        seen.add(key)
        kind, confidence = _classify(statement)
        elements.append(BriefElement(kind=kind, text=statement, confidence=confidence))
    return elements


def coverage_gaps(elements: list[BriefElement]) -> list[str]:
    """Note which element kinds are absent — useful for flagging thin briefs."""
    present = {e.kind for e in elements}
    notes: list[str] = []
    if ElementKind.USER not in present:
        notes.append("No target user or segment is named in the brief — questions assume a generic user.")
    if ElementKind.METRIC not in present:
        notes.append("No success metric is stated — it is hard to tie questions to a measurable outcome.")
    if ElementKind.DECISION not in present:
        notes.append("No explicit decision is stated — confirm what product choice this research will inform.")
    if ElementKind.ASSUMPTION not in present:
        notes.append("No assumptions are surfaced — consider what beliefs the brief takes for granted.")
    return notes
