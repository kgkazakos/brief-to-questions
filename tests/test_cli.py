import json

from click.testing import CliRunner

from brief_to_questions.cli import cli

BRIEF = (
    "We assume users trust suggestions.\n"
    "We need to decide whether to ship full replies.\n"
    "Why do agents feel replies sound impersonal?\n"
)


def test_analyze_no_llm_table():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--no-llm"], input=BRIEF)
    assert result.exit_code == 0
    assert "Research questions" in result.output


def test_analyze_json_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--no-llm", "--json-output"], input=BRIEF)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "questions" in data
    assert data["llm_backend"] is None
    assert len(data["questions"]) >= 2


def test_analyze_requires_input():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--no-llm"], input="")
    assert result.exit_code != 0


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "brief-to-questions" in result.output
