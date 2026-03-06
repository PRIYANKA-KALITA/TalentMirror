#!pip install langchain_groq groq flask_wtf flask_sqlalchemy python-docx pdfminer.six

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from config import Config
from forms import UploadResumeForm, AnswerForm, ROLE_CHOICES
from llm_groq import GroqLLM
from models import db, Candidate, Resume, InterviewSession, Question, Answer, Report
from resume_parser import allowed_file, extract_resume_text
from question_engine import generate_questions
from scoring import score_and_profile
from benchmarking import compute_benchmark
from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for
import sqlite3
import requests
import re
from werkzeug.utils import secure_filename
from datetime import datetime


os.environ["GROQ_API_KEY"] = "Your GROQ API KEY"


    
    





def create_app() -> Flask:
    load_dotenv()

    # Optional: allow template/static override via env (useful in Colab/Drive)
    template_folder = os.environ.get("TEMPLATE_FOLDER")
    static_folder = os.environ.get("STATIC_FOLDER")

    if template_folder or static_folder:
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)

    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"] = "/tmp/uploads"

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.get("/")
    @app.post("/")
    def index():
        form = UploadResumeForm()
        if form.validate_on_submit():
            f = form.resume_file.data
            filename = secure_filename(f.filename or "resume")
            if not allowed_file(filename):
                flash("Only PDF and DOCX resumes are allowed.", "danger")
                return render_template("index.html", form=form, iv_session=None)

            stored_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{int(datetime.utcnow().timestamp())}_{filename}")
            f.save(stored_path)

            try:
                resume_text = extract_resume_text(stored_path)
                if len(resume_text.strip()) < 200:
                    raise ValueError("Resume text extraction produced too little text.")
            except Exception as e:
                flash(f"Could not parse resume. Try a different file. ({e})", "danger")
                try:
                    os.remove(stored_path)
                except OSError:
                    pass
                return render_template("index.html", form=form, iv_session=None)

            cand = Candidate(full_name=form.full_name.data.strip(), email=(form.email.data or "").strip() or None)
            db.session.add(cand)
            db.session.flush()

            res = Resume(
                candidate_id=cand.id,
                filename=filename,
                stored_path=stored_path,
                extracted_text=resume_text,
            )
            db.session.add(res)
            db.session.flush()

            session = InterviewSession(
                candidate_id=cand.id,
                resume_id=res.id,
                role_target=form.role_target.data,
                status="QUESTIONS_READY",
                current_index=1,
            )
            db.session.add(session)
            db.session.flush()

            try:
                llm = GroqLLM(api_key=app.config.get("GROQ_API_KEY"), model=app.config.get("GROQ_MODEL"))
                qs = generate_questions(resume_text=resume_text, role_target=session.role_target, llm=llm)
            except Exception as e:
                flash(f"Question generation failed. Check GROQ_API_KEY and model. ({e})", "danger")
                db.session.rollback()
                return render_template("index.html", form=form, iv_session=None)

            for q in qs:
                db.session.add(Question(
                    session_id=session.id,
                    q_index=q["q_index"],
                    question_text=q["question_text"],
                    competency_tags=json.dumps(q.get("competency_tags", [])),
                ))

            session.status = "IN_PROGRESS"
            db.session.commit()

            return redirect(url_for("interview", session_id=session.id))

        return render_template("index.html", form=form, iv_session=None)

    @app.get("/interview/<int:session_id>")
    @app.post("/interview/<int:session_id>")
    def interview(session_id: int):
        iv_session = InterviewSession.query.get_or_404(session_id)

        if iv_session.status == "COMPLETED":
            return redirect(url_for("report", session_id=iv_session.id))

        questions = iv_session.questions
        if not questions or len(questions) < 10:
            flash("Interview questions are missing. Please restart.", "danger")
            return redirect(url_for("index"))

        current_idx = max(1, min(10, iv_session.current_index))
        current_q = next((q for q in questions if q.q_index == current_idx), None)
        if current_q is None:
            flash("Could not find current question. Restart the interview.", "danger")
            return redirect(url_for("index"))

        form = AnswerForm()

        if form.validate_on_submit():
            ans = Answer(question_id=current_q.id, answer_text=form.answer.data.strip())
            db.session.add(ans)

            if current_idx >= 10:
                iv_session.status = "COMPLETED"
                iv_session.completed_at = datetime.utcnow()
                iv_session.current_index = 10
                db.session.commit()

                _ensure_report(app, iv_session.id)
                return redirect(url_for("report", session_id=iv_session.id))

            iv_session.current_index = current_idx + 1
            db.session.commit()
            return redirect(url_for("interview", session_id=iv_session.id))

        existing_answer = Answer.query.filter_by(question_id=current_q.id).order_by(Answer.created_at.desc()).first()
        if request.method == "GET" and existing_answer:
            form.answer.data = existing_answer.answer_text

        return render_template(
            "interview.html",
            iv_session=iv_session,
            candidate=iv_session.candidate,
            role_target=iv_session.role_target,
            q_index=current_idx,
            question=current_q,
            form=form,
        )

    @app.get("/report/<int:session_id>")
    def report(session_id: int):
        iv_session = InterviewSession.query.get_or_404(session_id)
        if iv_session.status != "COMPLETED":
            flash("Interview not completed yet.", "warning")
            return redirect(url_for("interview", session_id=iv_session.id))

        rep = iv_session.report
        if rep is None:
            _ensure_report(app, iv_session.id)
            rep = iv_session.report

        profile = json.loads(rep.profile_json)
        benchmark = json.loads(rep.benchmark_json)

        return render_template(
            "report.html",
            iv_session=iv_session,
            candidate=iv_session.candidate,
            resume=iv_session.resume,
            profile=profile,
            benchmark=benchmark,
        )

    @app.get("/restart/<int:session_id>")
    def restart(session_id: int):
        iv_session = InterviewSession.query.get_or_404(session_id)
        for q in iv_session.questions:
            Answer.query.filter_by(question_id=q.id).delete()
        if iv_session.report:
            db.session.delete(iv_session.report)
        iv_session.status = "IN_PROGRESS"
        iv_session.current_index = 1
        iv_session.completed_at = None
        db.session.commit()
        flash("Interview restarted.", "info")
        return redirect(url_for("interview", session_id=iv_session.id))

    return app

def _ensure_report(app: Flask, session_id: int) -> None:
    iv_session = InterviewSession.query.get(session_id)
    if iv_session is None or iv_session.report is not None:
        return

    qas = []
    for q in iv_session.questions:
        a = Answer.query.filter_by(question_id=q.id).order_by(Answer.created_at.desc()).first()
        qas.append((q.question_text, (a.answer_text if a else "")))

    llm = GroqLLM(api_key=app.config.get("GROQ_API_KEY"), model=app.config.get("GROQ_MODEL"))
    profile = score_and_profile(
        resume_text=iv_session.resume.extracted_text,
        role_target=iv_session.role_target,
        qas=qas,
        llm=llm,
    )
    benchmark = compute_benchmark(profile.get("competency_scores", {}), role_target=iv_session.role_target)

    rep = Report(
        session_id=iv_session.id,
        profile_json=json.dumps(profile, ensure_ascii=False),
        benchmark_json=json.dumps(benchmark, ensure_ascii=False),
    )
    db.session.add(rep)
    db.session.commit()


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
