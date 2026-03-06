from __future__ import annotations

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Candidate(db.Model):
    __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    resumes = db.relationship("Resume", backref="candidate", lazy=True, cascade="all, delete-orphan")
    sessions = db.relationship("InterviewSession", backref="candidate", lazy=True, cascade="all, delete-orphan")

class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(512), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sessions = db.relationship("InterviewSession", backref="resume", lazy=True, cascade="all, delete-orphan")

class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False)

    role_target = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(30), default="QUESTIONS_READY", nullable=False)  # QUESTIONS_READY | IN_PROGRESS | COMPLETED
    current_index = db.Column(db.Integer, default=1, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    questions = db.relationship("Question", backref="session", lazy=True, cascade="all, delete-orphan", order_by="Question.q_index")
    report = db.relationship("Report", backref="session", uselist=False, cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id"), nullable=False)
    q_index = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    competency_tags = db.Column(db.Text, nullable=False, default="[]")  # JSON string

    answers = db.relationship("Answer", backref="question", lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id"), nullable=False, unique=True)

    profile_json = db.Column(db.Text, nullable=False)   # JSON string
    benchmark_json = db.Column(db.Text, nullable=False) # JSON string

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
