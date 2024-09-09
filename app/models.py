from .database import db
from datetime import datetime

class Visitor(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    first_visit = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)

class Participant(db.Model):
    __tablename__ = "participant"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))

class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255))
    option_1 = db.Column(db.String(255))  # 추가: 첫 번째 선택지
    option_2 = db.Column(db.String(255))  # 추가: 두 번째 선택지
    type = db.Column(db.String(2))  # 추가: MBTI 유형 (예: 'IE', 'SN', 'TF', 'JP')
    order_num = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))
    chosen_answer = db.Column(db.String(255))

    participant = db.relationship("Participant", backref="quizzes")
    question = db.relationship("Question", backref="quizzes")