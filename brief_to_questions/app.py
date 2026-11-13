"""Streamlit UI for brief-to-questions.

Run with:  streamlit run brief_to_questions/app.py

Visual language matches the rest of the CPR Orbital Series: DM Sans for body,
DM Mono for code/labels, a calm light theme with a single warm accent.
"""

from __future__ import annotations

import json

import streamlit as st

from brief_to_questions.llm import available_backends
from brief_to_questions.models import Severity
from brief_to_questions.pipeline import analyse

st.set_page_config(page_title="brief-to-questions", page_icon="🛰", layout="wide")

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap');
html, body, [class*="css"], .stMarkdown, .stTextArea textarea { font-family: 'DM Sans', sans-serif; }
code, .mono, .stCode, pre { font-family: 'DM Mono', monospace !important; }
.bq-title { font-size: 26px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 2px; }
.bq-sub { color: #6b6b6b; font-size: 13px; font-family: 'DM Mono', monospace; margin-bottom: 8px; }
.bq-card { border: 1px solid #e7e4dc; border-left: 3px solid #D85A30; border-radius: 8px;
           padding: 14px 16px; margin-bottom: 10px; background: #fffdf9; }
.bq-q { font-size: 15px; font-weight: 500; color: #1c1c1c; margin-bottom: 6px; }
.bq-meta { font-size: 12px; color: #6b6b6b; font-family: 'DM Mono', monospace; }
.bq-pill { display:inline-block; font-family:'DM Mono',monospace; font-size:11px; padding:1px 8px;
           border-radius:99px; border:1px solid #d9d4c8; color:#5f5e5a; margin-right:5px; }
.bq-pill.p1 { background:#fbe9e1; color:#993c1d; border-color:#f3c4b2; }
.bq-pill.p2 { background:#faf0e3; color:#854f0b; border-color:#ecd2a8; }
.bq-flag-warning { color:#854f0b; font-size:12px; }
.bq-flag-info { color:#8a8a8a; font-size:12px; }
.bq-flag-critical { color:#993c1d; font-size:12px; font-weight:600; }
.bq-rationale { font-size:12.5px; color:#555; margin-top:6px; }
</style>
"""

SAMPLE = """# Brief: Smart Reply for Team Inbox

## Goal
We want to reduce the time support agents spend writing repetitive replies so that they can handle more tickets per shift.

## Target users
Customer support agents at SMB companies who handle 40+ tickets a day.

## Assumptions
We assume agents will trust AI-suggested replies and edit them rather than ignore them.
We believe the biggest time sink is typing, not deciding what to say.

## Success metric
Reduce median handle time by 20% within one quarter.

## Decision
Should we ship one-click full replies, or only sentence-level suggestions?

## Open questions
We don't know whether agents feel suggested replies make them sound impersonal.
"""

st.markdown(_CSS, unsafe_allow_html=True)

st.markdown('<div class="bq-title">brief-to-questions</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="bq-sub">Turn a product brief into crisp, answerable, method-mapped research questions · '
    "CPR Orbital Series</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Engine")
    use_llm = st.toggle("LLM enrichment", value=True, help="On by default. Off uses the offline rule-based core.")
    backend = st.selectbox(
        "Backend",
        available_backends(),
        format_func=lambda b: {"anthropic": "Claude Opus", "gemini": "Gemini 4 Argon", "openai": "GPT-5.5"}.get(b, b),
        disabled=not use_llm,
    )
    st.caption("Backends ship on by default and run through LiteLLM. Set the matching API key in your environment.")
    st.markdown("---")
    st.caption("Part of the 40-tool CPR Orbital Series — shipping almost daily.")

left, right = st.columns([1, 1.25], gap="large")

with left:
    st.markdown("#### Paste a brief")
    brief = st.text_area("Brief", value=SAMPLE, height=420, label_visibility="collapsed")
    run = st.button("Generate research questions", type="primary", use_container_width=True)

with right:
    st.markdown("#### Research questions & recommended methods")
    if run and brief.strip():
        warnings: list[str] = []
        with st.spinner("Reading the brief…"):
            analysis = analyse(brief, use_llm=use_llm, backend=backend, on_warning=warnings.append)

        for w in warnings:
            st.warning(w)

        engine = analysis.llm_backend or "rule-based (offline)"
        st.caption(f"{analysis.summary}  ·  engine: {engine}")

        if analysis.coverage_notes:
            with st.expander(f"Coverage gaps ({len(analysis.coverage_notes)})", expanded=False):
                for note in analysis.coverage_notes:
                    st.markdown(f"- {note}")

        for q in analysis.questions:
            pill_cls = "p1" if q.priority == 1 else ("p2" if q.priority == 2 else "")
            flags_html = ""
            for f in q.flags:
                cls = {
                    Severity.WARNING: "bq-flag-warning",
                    Severity.INFO: "bq-flag-info",
                    Severity.CRITICAL: "bq-flag-critical",
                }[f.severity]
                flags_html += f'<div class="{cls}">⚑ {f.message}</div>'
            st.markdown(
                f"""
                <div class="bq-card">
                    <div class="bq-q">{q.text}</div>
                    <span class="bq-pill {pill_cls}">P{q.priority}</span>
                    <span class="bq-pill">{q.method.value}</span>
                    <span class="bq-pill">{q.question_type.value}</span>
                    <div class="bq-rationale"><b>Why this method:</b> {q.method_rationale}</div>
                    <div class="bq-meta" style="margin-top:6px;">Informs: {q.informs_decision}</div>
                    {flags_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.download_button(
            "Download JSON",
            data=json.dumps(analysis.to_dict(), indent=2),
            file_name="research-questions.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.info("Paste a brief on the left and click **Generate research questions**.")
