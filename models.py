from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    google_id = db.Column(db.String(100), unique=True)
    avatar_url = db.Column(db.String(500))
    college = db.Column(db.String(200))
    course = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)
    target_roles = db.Column(db.Text, default='[]')  # JSON list
    skills = db.Column(db.Text, default='[]')        # JSON list
    certifications = db.Column(db.Text, default='[]')
    resume_text = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    applications = db.relationship('Application', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    readiness_scores = db.relationship('ReadinessScore', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    mock_interviews = db.relationship('MockInterview', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_plans = db.relationship('StudyPlan', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_target_roles(self):
        try: return json.loads(self.target_roles or '[]')
        except: return []

    def get_skills(self):
        try: return json.loads(self.skills or '[]')
        except: return []

    def get_certifications(self):
        try: return json.loads(self.certifications or '[]')
        except: return []

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'college': self.college, 'course': self.course,
            'graduation_year': self.graduation_year,
            'target_roles': self.get_target_roles(),
            'skills': self.get_skills(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    package_lpa = db.Column(db.Float)
    location = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Applied')  # Applied, In Progress, Selected, Rejected, Offered
    applied_date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)
    job_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rounds = db.relationship('Round', backref='application', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'company': self.company, 'role': self.role,
            'package_lpa': self.package_lpa, 'location': self.location,
            'status': self.status, 'applied_date': str(self.applied_date),
            'notes': self.notes, 'job_link': self.job_link,
            'rounds': [r.to_dict() for r in self.rounds]
        }


class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    round_type = db.Column(db.String(100))  # Aptitude, Technical, HR, Managerial, GD, Assignment
    status = db.Column(db.String(50), default='Pending')  # Pending, Passed, Failed, Absent
    round_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    order_num = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id, 'round_type': self.round_type,
            'status': self.status, 'round_date': str(self.round_date) if self.round_date else None,
            'notes': self.notes, 'order_num': self.order_num
        }


class ReadinessScore(db.Model):
    __tablename__ = 'readiness_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_score = db.Column(db.Float, default=0.0)
    skills_score = db.Column(db.Float, default=0.0)      # 30%
    cert_score = db.Column(db.Float, default=0.0)         # 20%
    mock_score = db.Column(db.Float, default=0.0)         # 15%
    resume_score = db.Column(db.Float, default=0.0)       # 15%
    interview_score = db.Column(db.Float, default=0.0)    # 10%
    consistency_score = db.Column(db.Float, default=0.0)  # 10%
    improvement_tips = db.Column(db.Text, default='[]')
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_tips(self):
        try: return json.loads(self.improvement_tips or '[]')
        except: return []


class MockInterview(db.Model):
    __tablename__ = 'mock_interviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(200))
    question = db.Column(db.Text)
    user_answer = db.Column(db.Text)
    ai_feedback = db.Column(db.Text)
    self_rating = db.Column(db.Integer)  # 1-5
    ai_rating = db.Column(db.Float)
    category = db.Column(db.String(100))  # Technical, HR, Aptitude, Behavioral
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudyPlan(db.Model):
    __tablename__ = 'study_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    target_role = db.Column(db.String(200))
    days_left = db.Column(db.Integer)
    weak_areas = db.Column(db.Text, default='[]')
    plan_content = db.Column(db.Text)  # JSON structured plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_weak_areas(self):
        try: return json.loads(self.weak_areas or '[]')
        except: return []
