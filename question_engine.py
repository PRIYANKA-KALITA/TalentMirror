from __future__ import annotations
from typing import Dict, List

from llm_groq import GroqLLM, DEFAULT_SYSTEM

ROLE_HINTS = {
    "backend": "Backend Developer (APIs, databases, backend architecture, performance, security).",
    "frontend": "Frontend Developer (UI, JS/TS, accessibility, performance, UX, React/Vue/Angular).",
    "fullstack": "Full Stack Developer (frontend + backend + system design + deployment).",
    "data": "Data Engineer / Analyst (SQL, pipelines, modeling, data quality, warehousing).",
    "devops": "DevOps / Cloud Engineer (CI/CD, cloud, containers, observability, reliability).",
    "aiml": "AI/ML Engineer (Python, ML fundamentals, data preprocessing, feature engineering, model training, evaluation metrics, overfitting, deployment basics, MLOps, monitoring/drift).",  # ✅ added
}

def generate_questions(resume_text: str, role_target: str, llm: GroqLLM) -> List[Dict]:
    role_desc = ROLE_HINTS.get(role_target, role_target)

    user_prompt = f"""You will receive a candidate resume text. Create exactly 10 interview questions tailored to:
- The candidate's actual skills and projects in the resume
- The target role: {role_desc}

Rules:
- Make questions college-level / entry to mid-level professional, but adaptive to the resume.
- Include a balanced mix:
  * 4 technical depth (based on resume stack)
  * 2 problem-solving/debugging
  * 2 system design or architecture (scaled to their seniority)
  * 2 behavioral / collaboration
- Each question must include competency_tags (2-4 short tags).
- Output STRICT JSON with this schema:
{{
  "questions": [
    {{
      "q_index": 1,
      "question_text": "....",
      "competency_tags": ["tag1","tag2"]
    }}
  ]
}}

Resume:
""" + resume_text[:12000]

    data = llm.chat_json([
        {"role": "system", "content": DEFAULT_SYSTEM},
        {"role": "user", "content": user_prompt},
    ])

    questions = data.get("questions", [])
    cleaned = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if "question_text" not in q:
            continue
        cleaned.append({
            "q_index": int(q.get("q_index", len(cleaned) + 1)),
            "question_text": str(q["question_text"]).strip(),
            "competency_tags": q.get("competency_tags", []),
        })

    cleaned = sorted(cleaned, key=lambda x: x["q_index"])[:10]

    # Safety fallback: pad if fewer than 10 returned
    while len(cleaned) < 10:
        idx = len(cleaned) + 1
        cleaned.append({
            "q_index": idx,
            "question_text": f"Tell me about a project from your resume you are most proud of. What trade-offs did you make? (Q{idx})",
            "competency_tags": ["communication", "ownership"],
        })

    # Normalize indices 1..10
    for i, q in enumerate(cleaned, start=1):
        q["q_index"] = i

    return cleaned