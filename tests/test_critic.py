from brief_to_questions.critic import critique
from brief_to_questions.models import Severity


def _codes(text):
    return {f.code for f in critique(text)}


def test_leading_flag():
    assert "leading" in _codes("Don't you find the old layout frustrating?")


def test_double_barrelled_flag():
    assert "double_barrelled" in _codes("Do users want faster search and do they need filters?")


def test_vague_flag():
    assert "vague" in _codes("How is the overall user experience?")


def test_absolute_flag():
    assert "absolute" in _codes("Do all users always read the tooltip?")


def test_closed_flag():
    assert "closed" in _codes("Do users like the feature?")


def test_speculative_flag():
    assert "speculative" in _codes("What is your ideal future workflow?")


def test_clean_question_has_no_flags():
    assert critique("How do support agents decide which reply template to reuse?") == []


def test_flag_carries_severity():
    flags = critique("Don't you love the new design?")
    assert all(isinstance(f.severity, Severity) for f in flags)
