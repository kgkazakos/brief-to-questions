import json

import pytest

from brief_to_questions import llm
from brief_to_questions.models import BriefElement, ElementKind, ResearchMethod


def test_parse_json_array_strips_fences():
    raw = "```json\n[{\"text\": \"Why do users churn?\"}]\n```"
    rows = llm._parse_json_array(raw)
    assert rows[0]["text"] == "Why do users churn?"


def test_parse_json_array_extracts_embedded_array():
    raw = 'Here you go: [{"text": "x"}] thanks!'
    assert llm._parse_json_array(raw) == [{"text": "x"}]


def test_coerce_method_exact_and_keyword():
    assert llm._coerce_method("Survey") == ResearchMethod.SURVEY
    assert llm._coerce_method("a moderated usability session") == ResearchMethod.USABILITY_TEST
    assert llm._coerce_method("unknown thing") == ResearchMethod.INTERVIEW


def test_resolve_model_maps_backend_names():
    assert llm.resolve_model("anthropic") == llm.DEFAULT_MODELS["anthropic"]
    assert llm.resolve_model("openai/gpt-4o") == "openai/gpt-4o"


def test_available_backends():
    assert set(llm.available_backends()) == {"anthropic", "gemini", "openai"}


class _FakePrediction:
    def __init__(self, payload):
        self.questions_json = payload


class _FakeProgram:
    def __init__(self, payload):
        self._payload = payload

    def __call__(self, **kwargs):
        return _FakePrediction(self._payload)


def test_enrich_with_mocked_program(monkeypatch):
    payload = json.dumps(
        [
            {
                "text": "How do agents decide whether to trust a suggested reply?",
                "method": "Generative interviews",
                "method_rationale": "Trust is about reasoning, which needs depth.",
                "informs_decision": "Whether to ship full one-click replies",
                "priority": 1,
            }
        ]
    )
    monkeypatch.setattr(llm, "_build_program", lambda: _FakeProgram(payload))
    monkeypatch.setattr(llm, "_configure", lambda backend, temperature=0.3: backend)

    elements = [BriefElement(kind=ElementKind.ASSUMPTION, text="We assume agents trust replies.")]
    questions = llm.enrich("brief text", elements, backend="anthropic")
    assert len(questions) == 1
    q = questions[0]
    assert q.llm_enriched is True
    assert q.method == ResearchMethod.INTERVIEW
    assert q.priority == 1


def test_enrich_raises_when_program_fails(monkeypatch):
    def boom():
        raise ImportError("no dspy")

    monkeypatch.setattr(llm, "_build_program", boom)
    with pytest.raises(RuntimeError):
        llm.enrich("brief", [], backend="anthropic")
