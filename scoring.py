from __future__ import annotations
from typing import Dict, List, Tuple

from llm_groq import GroqLLM, DEFAULT_SYSTEM
from question_engine import ROLE_HINTS

COMPETENCIES = [
    "technical_depth",
    "problem_solving",
    "system_design",
    "communication",
    "role_fit",
]

def score_and_profile(
    resume_text: str,
    role_target: str,
    qas: List[Tuple[str, str]],
    llm: GroqLLM,
) -> Dict:
    role_desc = ROLE_HINTS.get(role_target, role_target)

    # Build a compact Q&A list
    qa_blob = []
    for i, (q, a) in enumerate(qas, start=1):
        qa_blob.append(f"Q{i}: {q}\nA{i}: {a}")
    qa_text = "\n\n".join(qa_blob)

    user_prompt = f"""You are evaluating a candidate for the role: {role_desc}.
Use the resume and their answers to 10 questions.

Return STRICT JSON with this schema:
{{
  "overall_summary": "3-6 sentences",
  "strengths": ["...","...","..."],
  "gaps": ["...","...","..."],
  "recommended_next_steps": ["...","...","..."],
  "competency_scores": {{
    "technical_depth": 0-100,
    "problem_solving": 0-100,
    "system_design": 0-100,
    "communication": 0-100,
    "role_fit": 0-100
  }},
  "per_question": [
    {{
      "q_index": 1,
      "score_1_to_5": 1-5,
      "notes": "short",
      "improvement_tip": "short"
    }}
  ]
}}

Scoring guidance:
- Be fair and consistent; scores should match evidence from the answers.
- If answer is empty/vague, score low.
- If answer shows clear reasoning and correctness, score high.

Resume (trimmed):
{resume_text[:9000]}

Interview Q&A:
{qa_text[:14000]}
"""

    data = llm.chat_json([
        {"role": "system", "content": DEFAULT_SYSTEM},
        {"role": "user", "content": user_prompt},
    ])

    # basic shape checks + defaults
    comp = data.get("competency_scores", {}) or {}
    data["competency_scores"] = {k: int(_clamp(comp.get(k, 50), 0, 100)) for k in COMPETENCIES}

    strengths = data.get("strengths") or []
    gaps = data.get("gaps") or []
    steps = data.get("recommended_next_steps") or []

    data["strengths"] = [str(x) for x in strengths][:5]
    data["gaps"] = [str(x) for x in gaps][:5]
    data["recommended_next_steps"] = [str(x) for x in steps][:6]
    data["overall_summary"] = str(data.get("overall_summary", "")).strip()

    pq = data.get("per_question") or []
    cleaned_pq = []
    for i, item in enumerate(pq, start=1):
        if not isinstance(item, dict):
            continue
        cleaned_pq.append({
            "q_index": int(item.get("q_index", i)),
            "score_1_to_5": int(_clamp(item.get("score_1_to_5", 3), 1, 5)),
            "notes": str(item.get("notes", "")).strip(),
            "improvement_tip": str(item.get("improvement_tip", "")).strip(),
        })
    cleaned_pq = sorted(cleaned_pq, key=lambda x: x["q_index"])[:10]
    while len(cleaned_pq) < 10:
        idx = len(cleaned_pq) + 1
        cleaned_pq.append({
            "q_index": idx,
            "score_1_to_5": 3,
            "notes": "Insufficient scoring details returned; defaulted to neutral.",
            "improvement_tip": "Add more specifics and concrete examples.",
        })
    for i, item in enumerate(cleaned_pq, start=1):
        item["q_index"] = i
    data["per_question"] = cleaned_pq
    return data

def _clamp(x, lo, hi):
    try:
        x = float(x)
    except Exception:
        x = lo
    return max(lo, min(hi, x))
