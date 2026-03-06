from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired

ROLE_CHOICES = [
    ("backend", "Backend Developer"),
    ("frontend", "Frontend Developer"),
    ("fullstack", "Full Stack Developer"),
    ("data", "Data Engineer / Analyst"),
    ("devops", "DevOps / Cloud Engineer"),
    ("aiml", "AI/ML Engineer"),
]

class UploadResumeForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email (optional)", validators=[Optional(), Email(), Length(max=255)])
    role_target = SelectField("Target role", choices=ROLE_CHOICES, validators=[DataRequired()])
    resume_file = FileField(
        "Upload resume (PDF/DOCX)",
        validators=[
            FileRequired(),
            FileAllowed(["pdf", "docx"], "Only PDF and DOCX files are allowed."),
        ],
    )
    submit = SubmitField("Generate Interview Questions")

class AnswerForm(FlaskForm):
    answer = TextAreaField("Your answer", validators=[DataRequired(), Length(min=10, max=4000)])
    submit = SubmitField("Save & Next")