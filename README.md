# TalentMirror (Flask + Groq) — Resume-based Interview, Profiling & Benchmarking

This is a college-level project that:
1. Uploads a resume (PDF/DOCX), extracts text
2. Uses Groq LLM to generate **10 tailored interview questions**
3. Runs an interview flow where the browser reads questions via **Text-to-Speech**
4. Collects answers, then generates:
   - Candidate profile (strengths, gaps, next steps)
   - Benchmarking percentiles (synthetic baseline for demo)

## 1) Setup

### Prereqs
- Python 3.9+
- A Groq API key

### Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure environment
Copy `.env.example` to `.env` and set:
- `GROQ_API_KEY=...`
- optional `GROQ_MODEL=llama-3.3-70b-versatile`

```bash
cp .env.example .env
```

## 2) Run
```bash
python app.py
```
Open http://127.0.0.1:5000

## 3) Notes
- TTS uses the browser Web Speech API (speechSynthesis). Some browsers/OS voices differ.
- Benchmarking is a synthetic baseline in `benchmarking.py` for demo purposes.
  Replace it with real distributions once you collect enough data.

## 4) Project structure
- `app.py` — Flask routes and flow
- `models.py` — SQLAlchemy models (SQLite by default)
- `resume_parser.py` — PDF/DOCX text extraction
- `question_engine.py` — question generation via Groq (JSON mode)
- `scoring.py` — scoring + profiling via Groq (JSON mode)
- `benchmarking.py` — percentile computation
- `templates/` — HTML pages
- `static/` — CSS + JS (TTS logic)
