# brief-to-questions

**Turn a product brief into crisp, answerable, methodologically sound research questions — each with a recommended method.**

A product brief usually arrives full of goals, assumptions, and a decision that needs making — but not a single research question. Turning that brief into questions a team can actually answer is collaborative, skilled work, and it is the step most often skipped under time pressure. `brief-to-questions` does the first pass for everyone at the table: it reads the brief, surfaces the assumptions and decisions hiding inside it, proposes research questions that are specific and non-leading, and recommends a method that can credibly answer each one. It gives a product trio — researcher, PM, designer — a shared, neutral draft to argue over, rather than a blank page.

It is the first tool in **Season 6 (Pre-study & impact)** of the [CPR Orbital Series](#part-of-the-cpr-ecosystem).

---

## What it does

- **Extracts the brief's structure** — goals, assumptions, decisions, target users, success metrics, constraints, and open questions — so nothing important slips through.
- **Generates research questions** that are crisp, answerable, and free of leading or double-barrelled wording by construction.
- **Recommends a method for every question** (interview, survey, usability test, diary study, A/B test, and more) with a one-sentence rationale, so method choice is defensible rather than habitual.
- **Flags quality risks** — leading wording, vague abstractions, absolute framing, speculative "ideal future" questions — the way a careful reviewer would.
- **Names the decision each question informs** and assigns a decision-impact priority, so you research the things that actually change a call.
- **Surfaces coverage gaps** when a brief has no stated metric, user, or decision.

## What this is — and is not

This is a **drafting partner for the scoping stage**, not a replacement for research judgment. The questions it proposes are a starting point you edit, cut, and reorder — they encode reasonable defaults, not the context only you have. Method mappings are recommendations, not prescriptions. The quality flags are signals for your attention, not verdicts. The point is to get you to a defensible draft faster, so you spend your time on the judgment calls that matter.

## Install

```bash
pip install brief-to-questions            # core (runs fully offline)
pip install "brief-to-questions[llm]"     # + LLM enrichment (any backend)
pip install "brief-to-questions[ui]"      # + Streamlit app
```

Per-provider extras are also available: `[anthropic]`, `[openai]`, `[gemini]`.

## Usage

### CLI

LLM enrichment is **on by default**. Pass `--no-llm` for the deterministic offline core.

```bash
# From a file (LLM enrichment on)
brief-to-questions analyze brief.md

# Offline rule-based core, JSON for pipelines / CI
brief-to-questions analyze brief.md --no-llm --json-output

# Pick a backend
brief-to-questions analyze brief.md --backend gemini

# Pipe from stdin
cat brief.md | brief-to-questions analyze -

# Whole folder of briefs
brief-to-questions batch ./briefs --pattern "*.md"
```

### Python

```python
from brief_to_questions import analyse

analysis = analyse(open("brief.md").read(), use_llm=True, backend="anthropic")
for q in analysis.questions:
    print(f"[P{q.priority}] {q.text}  ·  {q.method.value}")
```

### Streamlit UI

```bash
streamlit run brief_to_questions/app.py
```

Paste a brief, pick a backend, and get prioritised, method-mapped questions you can download as JSON.

## LLM backends

Three backends ship **enabled by default**, all routed through [LiteLLM](https://github.com/BerriAI/litellm) via [DSPy](https://github.com/stanfordnlp/dspy) `ChainOfThought`:

| Backend     | Default model id (configurable)     |
|-------------|-------------------------------------|
| `anthropic` | `anthropic/claude-opus-4-7`         |
| `gemini`    | `gemini/gemini-3.1-pro-preview`     |
| `openai`    | `openai/gpt-5.5`                    |

The model ids are plain configuration in `brief_to_questions/llm.py` — point them at the exact model your account can call. Set the matching API key in your environment (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`). If a backend is unavailable for any reason, the tool falls back to the rule-based core automatically, so it never hard-fails.

## How it works

```
brief text
   │
   ├─ extractor.py   rule-based: brief → structured elements
   ├─ llm.py         optional: DSPy ChainOfThought → grounded questions
   ├─ generator.py   rule-based fallback: elements → questions
   ├─ methods.py     question shape → method + rationale
   ├─ critic.py      quality flags (leading / vague / double-barrelled / …)
   └─ pipeline.py    orchestration → BriefAnalysis
```

The rule-based core has zero third-party dependencies beyond `click` and `rich` and is fully deterministic, so the offline path and its tests never need an API key.

## Development

```bash
pip install -e ".[dev]"
ruff check brief_to_questions tests
pytest -q
```

## Part of the CPR Ecosystem

`brief-to-questions` is one of 40 open-source tools in the **CPR Orbital Series** — a portfolio of AI-native product-research infrastructure shipping almost daily through 2026, built by [Kostas Kazakos](https://github.com/kgkazakos) as part of **Computational Product Research (CPR)**.

It opens **Season 6 — Pre-study & impact**, and pairs naturally with:

- **[qual-sniffer](https://github.com/kgkazakos/qual-sniffer)** — detects methodological weaknesses in discussion guides and research plans.
- **[research-rubric](https://github.com/kgkazakos/research-rubric)** — evaluates qualitative research quality across saturation, bias, and evidence.
- **screener-generator** *(next in S6)* — turns a brief into recruitment screeners with quota logic.
- **study-planner** — AI-assisted study scoping, timeline, and resource estimation.

It is distinct from the core CPR research projects (CausalTrack, Synthetic User Council, Co-Reasoning Canvas), which are maintained separately.

## License

MIT © 2026 Kostas Kazakos
