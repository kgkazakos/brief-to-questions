"""Optional LLM enrichment for brief-to-questions.

The rule-based core always runs. This layer, when a backend is configured,
re-reads the brief with a language model and proposes sharper, better-grounded
research questions than templates can. It uses DSPy's ChainOfThought so the
reasoning that leads to each question is explicit rather than hidden.

Three backends ship enabled by default. The model identifiers below are plain
configuration: change them to whatever exact provider model id you have access
to. DSPy talks to all three through LiteLLM, so the call site is identical.

This module imports ``dspy`` lazily inside the functions that need it, so
importing the package (and running the offline core + its tests) never requires
the LLM dependencies to be installed.
"""

from __future__ import annotations

import json
import re

from .critic import critique
from .methods import classify_question_type
from .models import BriefElement, QuestionType, ResearchMethod, ResearchQuestion

# --- Configurable backend defaults --------------------------------------------
# These are the three backends enabled by default. They are configuration, not
# constants of nature: point them at the exact model id your account can call.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "anthropic/claude-opus-4-7",      # Claude Opus
    "gemini": "gemini/gemini-3.1-pro-preview",     # Gemini 3.1 Pro
    "openai": "openai/gpt-5.5",                    # GPT-5.5
}
DEFAULT_BACKEND = "anthropic"


def available_backends() -> list[str]:
    return list(DEFAULT_MODELS.keys())


def resolve_model(backend: str) -> str:
    """Map a friendly backend name to a model id, or pass through a full id."""
    if backend in DEFAULT_MODELS:
        return DEFAULT_MODELS[backend]
    return backend  # already a full litellm-style identifier


# --- DSPy signature (defined lazily so import never needs dspy) ---------------
def _build_program():
    import dspy

    class BriefToResearchQuestions(dspy.Signature):
        """Read a product brief and propose crisp, answerable, non-leading
        research questions. For each, name the single best research method, a
        one-sentence rationale for that method, the decision it informs, and a
        priority from 1 (highest decision impact) to 5. Avoid leading wording,
        double-barrelled questions, and speculative 'ideal future' questions.
        Respond ONLY with a JSON array, no prose, no markdown fences."""

        brief: str = dspy.InputField(desc="The raw PM brief or PRD text.")
        context: str = dspy.InputField(desc="Structured elements already detected in the brief.")
        questions_json: str = dspy.OutputField(
            desc=(
                "JSON array of objects with keys: text, method, method_rationale, "
                "informs_decision, priority (int 1-5)."
            )
        )

    return dspy.ChainOfThought(BriefToResearchQuestions)


def _configure(backend: str, temperature: float = 0.3):
    import dspy

    model = resolve_model(backend)
    lm = dspy.LM(model, temperature=temperature, max_tokens=2000)
    dspy.configure(lm=lm)
    return model


_METHOD_LOOKUP = {m.value.lower(): m for m in ResearchMethod}
_METHOD_KEYWORDS: list[tuple[str, ResearchMethod]] = [
    ("usability", ResearchMethod.USABILITY_TEST),
    ("survey", ResearchMethod.SURVEY),
    ("diary", ResearchMethod.DIARY_STUDY),
    ("field", ResearchMethod.FIELD_STUDY),
    ("contextual", ResearchMethod.FIELD_STUDY),
    ("card", ResearchMethod.CARD_SORT),
    ("tree test", ResearchMethod.CARD_SORT),
    ("concept", ResearchMethod.CONCEPT_TEST),
    ("a/b", ResearchMethod.AB_TEST),
    ("experiment", ResearchMethod.AB_TEST),
    ("analytic", ResearchMethod.ANALYTICS),
    ("literature", ResearchMethod.LITERATURE_REVIEW),
    ("secondary", ResearchMethod.LITERATURE_REVIEW),
    ("interview", ResearchMethod.INTERVIEW),
]


def _coerce_method(raw: str) -> ResearchMethod:
    low = (raw or "").strip().lower()
    if low in _METHOD_LOOKUP:
        return _METHOD_LOOKUP[low]
    for keyword, method in _METHOD_KEYWORDS:
        if keyword in low:
            return method
    return ResearchMethod.INTERVIEW


def _parse_json_array(raw: str) -> list[dict]:
    """Parse a model response into a list of dicts, tolerating code fences."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Model did not return a JSON array.")
    return data


def enrich(brief: str, elements: list[BriefElement], backend: str = DEFAULT_BACKEND) -> list[ResearchQuestion]:
    """Generate research questions for a brief using an LLM backend.

    Raises ``RuntimeError`` if dspy is unavailable or the call/parse fails, so
    the caller can fall back to the rule-based generator.
    """
    try:
        program = _build_program()
        _configure(backend)
    except ImportError as exc:  # dspy not installed
        raise RuntimeError(
            "LLM enrichment needs the optional dependencies. Install with "
            "`pip install 'brief-to-questions[llm]'`."
        ) from exc

    context = "\n".join(f"- [{e.kind.value}] {e.text}" for e in elements) or "(none detected)"
    try:
        prediction = program(brief=brief, context=context)
        rows = _parse_json_array(prediction.questions_json)
    except Exception as exc:  # noqa: BLE001 - surface any runtime/parse failure uniformly
        raise RuntimeError(f"LLM enrichment failed: {exc}") from exc

    questions: list[ResearchQuestion] = []
    for row in rows:
        text = str(row.get("text", "")).strip()
        if not text:
            continue
        qtype = classify_question_type(text)
        try:
            priority = int(row.get("priority", 3))
        except (TypeError, ValueError):
            priority = 3
        priority = min(5, max(1, priority))
        questions.append(
            ResearchQuestion(
                text=text,
                question_type=qtype if isinstance(qtype, QuestionType) else QuestionType.DESCRIPTIVE,
                method=_coerce_method(str(row.get("method", ""))),
                method_rationale=str(row.get("method_rationale", "")).strip(),
                informs_decision=str(row.get("informs_decision", "")).strip(),
                priority=priority,
                flags=critique(text),
                source="llm",
                llm_enriched=True,
            )
        )
    questions.sort(key=lambda q: q.priority)
    return questions
