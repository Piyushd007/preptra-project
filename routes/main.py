from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from flask_login import login_required, current_user
from models import db, Application, Round, ReadinessScore, MockInterview, User
from datetime import datetime, timedelta
from collections import defaultdict
import json, math

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    apps = current_user.applications.all()
    total = len(apps)
    selected = sum(1 for a in apps if a.status == 'Selected')
    in_progress = sum(1 for a in apps if a.status == 'In Progress')
    rejected = sum(1 for a in apps if a.status == 'Rejected')

    # Latest readiness score
    score = current_user.readiness_scores.order_by(ReadinessScore.calculated_at.desc()).first()
    readiness = round(score.total_score, 1) if score else 0

    # Recent applications
    recent_apps = current_user.applications.order_by(Application.created_at.desc()).limit(5).all()

    # Mock interview stats
    mocks = current_user.mock_interviews.all()
    avg_mock = round(sum(m.ai_rating for m in mocks if m.ai_rating) / max(len([m for m in mocks if m.ai_rating]), 1), 1)

    return render_template('dashboard.html',
        total_apps=total, selected=selected, in_progress=in_progress,
        rejected=rejected, readiness=readiness, recent_apps=recent_apps,
        mock_count=len(mocks), avg_mock=avg_mock
    )

@main_bp.route('/analytics')
@login_required
def analytics():
    apps = current_user.applications.all()
    # Status distribution
    status_counts = defaultdict(int)
    for a in apps: status_counts[a.status] += 1
    # Round failure analysis
    round_fails = defaultdict(int)
    round_total = defaultdict(int)
    for a in apps:
        for r in a.rounds:
            round_total[r.round_type] += 1
            if r.status == 'Failed': round_fails[r.round_type] += 1
    # Monthly applications
    monthly = defaultdict(int)
    for a in apps:
        if a.applied_date:
            key = a.applied_date.strftime('%b %Y')
            monthly[key] += 1
    # Readiness history
    scores = current_user.readiness_scores.order_by(ReadinessScore.calculated_at.asc()).limit(10).all()
    score_history = [{'date': s.calculated_at.strftime('%d %b'), 'score': s.total_score} for s in scores]
    # Company pipeline
    companies = [{'company': a.company, 'role': a.role, 'status': a.status, 'package': a.package_lpa} for a in apps[:20]]
    return render_template('analytics.html',
        status_counts=dict(status_counts),
        round_fails=dict(round_fails),
        round_total=dict(round_total),
        monthly=dict(monthly),
        score_history=score_history,
        companies=companies,
        total_apps=len(apps)
    )

@main_bp.route('/readiness')
@login_required
def readiness():
    score = current_user.readiness_scores.order_by(ReadinessScore.calculated_at.desc()).first()
    history = current_user.readiness_scores.order_by(ReadinessScore.calculated_at.desc()).limit(10).all()
    return render_template('readiness_score.html', score=score, history=history)

@main_bp.route('/api/compute-readiness', methods=['POST'])
@login_required
def compute_readiness():
    skills = current_user.get_skills()
    certs = current_user.get_certifications()
    apps = current_user.applications.all()
    mocks = current_user.mock_interviews.all()

    # Skills score (30%) - based on number of skills
    skills_score = min(len(skills) * 5, 100)

    # Cert score (20%)
    cert_score = min(len(certs) * 20, 100)

    # Mock score (15%)
    rated_mocks = [m for m in mocks if m.ai_rating]
    mock_score = round(sum(m.ai_rating * 20 for m in rated_mocks) / max(len(rated_mocks), 1), 1) if rated_mocks else 0

    # Resume score (15%)
    resume_score = 60 if current_user.resume_text else 0

    # Interview score (10%) - based on rounds passed
    total_rounds = sum(1 for a in apps for r in a.rounds)
    passed_rounds = sum(1 for a in apps for r in a.rounds if r.status == 'Passed')
    interview_score = round((passed_rounds / max(total_rounds, 1)) * 100, 1) if total_rounds else 0

    # Consistency score (10%) - based on regular applications
    recent = sum(1 for a in apps if a.applied_date and (datetime.utcnow().date() - a.applied_date).days <= 30)
    consistency_score = min(recent * 10, 100)

    total = round(
        skills_score * 0.30 +
        cert_score * 0.20 +
        mock_score * 0.15 +
        resume_score * 0.15 +
        interview_score * 0.10 +
        consistency_score * 0.10, 1
    )

    tips = []
    if skills_score < 60: tips.append("Add more skills to your profile — aim for at least 10-12 relevant skills.")
    if cert_score < 40: tips.append("Earn at least 2-3 industry certifications (Coursera, Google, AWS).")
    if mock_score < 60: tips.append("Practice more mock interviews. Target 70%+ score in technical rounds.")
    if resume_score < 80: tips.append("Upload and optimize your resume for ATS — get a 80+ resume score.")
    if interview_score < 50: tips.append("Focus on clearing more interview rounds. Work on weak areas.")
    if consistency_score < 40: tips.append("Apply to more companies regularly. Consistency = higher success rate.")

    score_obj = ReadinessScore(
        user_id=current_user.id,
        total_score=total,
        skills_score=skills_score,
        cert_score=cert_score,
        mock_score=mock_score,
        resume_score=resume_score,
        interview_score=interview_score,
        consistency_score=consistency_score,
        improvement_tips=json.dumps(tips)
    )
    db.session.add(score_obj)
    db.session.commit()
    return jsonify({
        'total': total, 'skills': skills_score, 'cert': cert_score,
        'mock': mock_score, 'resume': resume_score, 'interview': interview_score,
        'consistency': consistency_score, 'tips': tips
    })

@main_bp.route('/mock-interview')
@login_required
def mock_interview():
    sessions = current_user.mock_interviews.order_by(MockInterview.created_at.desc()).limit(20).all()
    return render_template('mock_interview.html', sessions=sessions)

@main_bp.route('/api/mock-question', methods=['POST'])
@login_required
def get_mock_question():
    data = request.get_json()
    role = data.get('role', 'Software Developer')
    category = data.get('category', 'Technical')

    questions_bank = {
        'Technical': [
            "Explain the difference between a stack and a queue with examples.",
            "What is the time complexity of quicksort? When does it perform worst?",
            "Explain OOPS concepts: polymorphism and encapsulation.",
            "What is a deadlock? How do you prevent it?",
            "Explain REST API principles and HTTP methods.",
            "What is normalization in databases? Explain 1NF, 2NF, 3NF.",
            "Write a function to reverse a linked list.",
            "What is the difference between process and thread?",
            "Explain how garbage collection works in your language.",
            "What is the difference between SQL and NoSQL databases?",
        ],
        'HR': [
            "Tell me about yourself.",
            "Where do you see yourself in 5 years?",
            "What are your strengths and weaknesses?",
            "Why do you want to work with us?",
            "Describe a challenging situation and how you handled it.",
            "How do you handle pressure and tight deadlines?",
            "Why are you leaving your current role / college?",
            "What motivates you?",
            "Describe a time you showed leadership.",
            "What are your salary expectations?",
        ],
        'Aptitude': [
            "If a train travels 360km in 4 hours, what is its speed?",
            "A bag contains 3 red, 4 blue, 2 green balls. Find probability of picking red.",
            "What number comes next: 2, 6, 12, 20, 30, ?",
            "Find the odd one out: 121, 144, 169, 196, 225, 289, 400",
            "A work takes 12 days for A and 18 days for B. How long together?",
        ],
        'Behavioral': [
            "Describe a project you're most proud of.",
            "Tell me about a time you disagreed with a team member.",
            "How do you prioritize tasks when working on multiple projects?",
            "Describe a time you learned from failure.",
            "Tell me about a time you went above and beyond.",
        ]
    }

    import random
    q_list = questions_bank.get(category, questions_bank['Technical'])
    question = random.choice(q_list)
    return jsonify({'question': question, 'category': category, 'role': role})

@main_bp.route('/api/mock-submit', methods=['POST'])
@login_required
def submit_mock():
    data = request.get_json()
    question = data.get('question', '')
    answer = data.get('answer', '')
    role = data.get('role', 'Software Developer')
    category = data.get('category', 'Technical')
    self_rating = data.get('self_rating', 3)

    ai_feedback = "Your answer demonstrates understanding of the concept. "
    ai_rating = 3.0

    # Simple rule-based scoring
    word_count = len(answer.split())
    if word_count > 100: ai_rating += 0.5; ai_feedback += "Good detail in your explanation. "
    if word_count > 200: ai_rating += 0.5; ai_feedback += "Comprehensive answer with examples. "
    if word_count < 30: ai_rating -= 1.0; ai_feedback += "Try to elaborate more with examples. "

    # Try AI feedback if configured
    try:
        from flask import current_app
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        if api_key and answer.strip():
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "You are an expert interviewer. Rate the answer 1-5 and give brief, constructive feedback in 2-3 sentences. Return JSON: {\"rating\": float, \"feedback\": string}"
                }, {
                    "role": "user",
                    "content": f"Question: {question}\nAnswer: {answer}\nRole: {role}, Category: {category}"
                }],
                max_tokens=200
            )
            result = json.loads(resp.choices[0].message.content)
            ai_rating = float(result.get('rating', ai_rating))
            ai_feedback = result.get('feedback', ai_feedback)
    except: pass

    ai_rating = max(1.0, min(5.0, ai_rating))

    mock = MockInterview(
        user_id=current_user.id, role=role, question=question,
        user_answer=answer, ai_feedback=ai_feedback,
        self_rating=int(self_rating), ai_rating=ai_rating, category=category
    )
    db.session.add(mock)
    db.session.commit()
    return jsonify({'feedback': ai_feedback, 'ai_rating': ai_rating, 'success': True})

@main_bp.route('/resources')
@login_required
def resources():
    resources_data = {
        'Software Developer': {
            'DSA': ['LeetCode', 'GeeksforGeeks', 'NeetCode.io'],
            'System Design': ['Grokking System Design', 'System Design Primer (GitHub)'],
            'Languages': ['Python Official Docs', 'JavaScript.info', 'Java Brains'],
            'Certifications': [
                {'name': 'Google IT Automation with Python', 'link': 'https://coursera.org', 'platform': 'Coursera'},
                {'name': 'AWS Cloud Practitioner', 'link': 'https://aws.amazon.com', 'platform': 'AWS'},
            ]
        },
        'Data Analyst': {
            'SQL': ['Mode Analytics SQL Tutorial', 'SQLZoo', 'W3Schools SQL'],
            'Python/R': ['Kaggle Learn', 'DataCamp', 'Towards Data Science'],
            'Tools': ['Tableau Public', 'Power BI Docs', 'Excel for Analysts'],
            'Certifications': [
                {'name': 'Google Data Analytics', 'link': 'https://coursera.org', 'platform': 'Coursera'},
                {'name': 'IBM Data Analyst', 'link': 'https://coursera.org', 'platform': 'Coursera'},
            ]
        },
        'Product Manager': {
            'Fundamentals': ['Lenny\'s Newsletter', 'Product School Blog', 'Mind the Product'],
            'Frameworks': ['RICE Scoring', 'OKRs Guide', 'Jobs-to-be-Done'],
            'Certifications': [
                {'name': 'Google Project Management', 'link': 'https://coursera.org', 'platform': 'Coursera'},
            ]
        }
    }
    return render_template('resources.html', resources=resources_data)

@main_bp.route('/profile')
@login_required
def profile():
    apps = current_user.applications.all()
    score = current_user.readiness_scores.order_by(ReadinessScore.calculated_at.desc()).first()
    return render_template('profile.html', score=score, total_apps=len(apps))
