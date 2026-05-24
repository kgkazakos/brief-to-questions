from pathlib import Path

from brief_to_questions import llm
from brief_to_questions.models import BriefAnalysis
from brief_to_questions.pipeline import analyse

FIXTURE = Path(__file__).parent / "fixtures" / "sample_brief.md"


def test_offline_pipeline_runs():
    analysis = analyse(FIXTURE.read_text(), use_llm=False)
    assert isinstance(analysis, BriefAnalysis)
    assert analysis.llm_backend is None
    assert len(analysis.questions) >= 3
    assert "rule-based" in analysis.summary


def test_to_dict_is_json_serialisable():
    import json

    analysis = analyse(FIXTURE.read_text(), use_llm=False)
    json.dumps(analysis.to_dict())  # should not raise


def test_llm_failure_falls_back_to_rule_based(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(llm, "enrich", boom)
    warnings = []
    analysis = analyse(FIXTURE.read_text(), use_llm=True, on_warning=warnings.append)
    assert analysis.llm_backend is None
    assert warnings  # a fallback warning was emitted
    assert len(analysis.questions) >= 3


def test_llm_path_used_when_available(monkeypatch):
    from brief_to_questions.models import QuestionType, ResearchMethod, ResearchQuestion

    def fake_enrich(brief, elements, backend="anthropic"):
        return [
            ResearchQuestion(
                text="How do agents judge a suggested reply?",
                question_type=QuestionType.EXPLORATORY,
                method=ResearchMethod.INTERVIEW,
                method_rationale="depth",
                informs_decision="ship decision",
                priority=1,
                llm_enriched=True,
            )
        ]

    monkeypatch.setattr(llm, "enrich", fake_enrich)
    analysis = analyse(FIXTURE.read_text(), use_llm=True, backend="anthropic")
    assert analysis.llm_backend == "anthropic"
    assert analysis.questions[0].llm_enriched is True
