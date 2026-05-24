from brief_to_questions.methods import classify_question_type, map_method
from brief_to_questions.models import QuestionType, ResearchMethod


def test_why_is_exploratory():
    assert classify_question_type("Why do users abandon checkout?") == QuestionType.EXPLORATORY


def test_can_users_is_evaluative():
    assert classify_question_type("Can users complete the setup without help?") == QuestionType.EVALUATIVE


def test_does_is_causal():
    assert classify_question_type("Does the new banner increase signups?") == QuestionType.CAUSAL


def test_default_is_descriptive():
    assert classify_question_type("What features do users rely on most?") == QuestionType.DESCRIPTIVE


def test_how_many_maps_to_survey():
    method, rationale = map_method("How many users use the export feature?", QuestionType.DESCRIPTIVE)
    assert method == ResearchMethod.SURVEY
    assert rationale


def test_task_success_maps_to_usability():
    method, _ = map_method("Can users complete the task on first try?", QuestionType.EVALUATIVE)
    assert method == ResearchMethod.USABILITY_TEST


def test_why_maps_to_interview():
    method, _ = map_method("Why do users prefer the old layout?", QuestionType.EXPLORATORY)
    assert method == ResearchMethod.INTERVIEW


def test_causal_fallback_is_ab_test():
    method, _ = map_method("Will this change move the metric?", QuestionType.CAUSAL)
    assert method == ResearchMethod.AB_TEST
