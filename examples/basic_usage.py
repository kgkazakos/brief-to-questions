"""Minimal example: analyse a brief offline (rule-based core, no API key needed).

Run:  python examples/basic_usage.py
"""

from brief_to_questions import analyse

BRIEF = """
# Brief: Onboarding redesign

Goal: We want to improve first-week activation for new users.
Target users: New self-serve signups on the free plan.
We assume new users abandon because the setup checklist is too long.
Success metric: Increase week-1 activation by 15%.
Decision: Should we cut the checklist to three steps or keep all seven?
We don't know which step causes the most drop-off.
"""

if __name__ == "__main__":
    # use_llm=False keeps this fully offline and deterministic for the example.
    analysis = analyse(BRIEF, use_llm=False)
    print(analysis.summary)
    print()
    for q in analysis.questions:
        print(f"[P{q.priority}] {q.text}")
        print(f"    method: {q.method.value}")
        if q.flags:
            for f in q.flags:
                print(f"    flag ({f.severity.value}): {f.message}")
        print()
