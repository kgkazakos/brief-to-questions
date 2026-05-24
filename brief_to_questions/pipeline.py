"""End-to-end pipeline: brief text in, structured analysis out.

By default the pipeline uses an LLM backend, because Kostas ships these tools
with enrichment on. If no backend is available (dependencies missing, no API
key, or the user passes ``use_llm=False``) it falls back to the deterministic
rule-based generator so the tool still produces a useful result offline.
"""

from __future__ import annotations

from . import llm
from .extractor import coverage_gaps, extract_elements
from .generator import generate_questions
from .models import BriefAnalysis, BriefElement, ResearchQuestion


def _summarise(elements: list[BriefElement], questions: list[ResearchQuestion], backend: str | None) -> str:
    kinds = {}
    for e in elements:
        kinds[e.kind.value] = kinds.get(e.kind.value, 0) + 1
    method_count = len({q.method for q in questions})
    engine = f"LLM enrichment ({backend})" if backend else "rule-based core"
    return (
        f"Extracted {len(elements)} brief elements and generated {len(questions)} "
        f"research questions across {method_count} methods using the {engine}. "
        f"Element mix: " + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())) + "."
    )


def analyse(
    brief: str,
    use_llm: bool = True,
    backend: str = llm.DEFAULT_BACKEND,
    on_warning=None,
) -> BriefAnalysis:
    """Analyse a brief and return a :class:`BriefAnalysis`.

    Parameters
    ----------
    brief:
        Raw PM brief / PRD text.
    use_llm:
        Whether to attempt LLM enrichment first (default True).
    backend:
        Which configured backend to use (``anthropic``, ``gemini``, ``openai``
        or a full litellm model id).
    on_warning:
        Optional callable invoked with a string if LLM enrichment fails and the
        pipeline falls back to the rule-based core.
    """
    elements = extract_elements(brief)
    used_backend: str | None = None
    questions: list[ResearchQuestion]

    if use_llm:
        try:
            questions = llm.enrich(brief, elements, backend=backend)
            used_backend = backend
            if not questions:
                raise RuntimeError("LLM returned no questions.")
        except RuntimeError as exc:
            if on_warning is not None:
                on_warning(f"{exc} Falling back to rule-based generation.")
            questions = generate_questions(elements)
    else:
        questions = generate_questions(elements)

    return BriefAnalysis(
        elements=elements,
        questions=questions,
        summary=_summarise(elements, questions, used_backend),
        coverage_notes=coverage_gaps(elements),
        llm_backend=used_backend,
    )
