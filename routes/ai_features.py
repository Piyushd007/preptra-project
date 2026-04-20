from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, ChatMessage, StudyPlan
import json
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

SKILL_MAP = {
    'Software Developer': {
        'required': ['Data Structures', 'Algorithms', 'OOP', 'Python or Java or C++', 'SQL', 'Git', 'REST APIs', 'System Design', 'OS Fundamentals', 'DBMS'],
        'good_to_have': ['React/Angular', 'Docker', 'AWS/GCP', 'Redis', 'Microservices', 'Kubernetes']
    },
    'Data Analyst': {
        'required': ['SQL', 'Python', 'Excel', 'Data Visualization', 'Statistics', 'Pandas', 'NumPy', 'Tableau or Power BI'],
        'good_to_have': ['Machine Learning', 'R', 'Apache Spark', 'A/B Testing', 'Looker']
    },
    'Product Manager': {
        'required': ['Market Research', 'Agile/Scrum', 'User Stories', 'Roadmapping', 'Excel', 'Communication', 'Wireframing', 'KPIs'],
        'good_to_have': ['SQL', 'Jira', 'Figma', 'A/B Testing', 'Go-to-Market Strategy']
    },
    'Marketing Executive': {
        'required': ['Digital Marketing', 'SEO/SEM', 'Content Writing', 'Social Media', 'Google Analytics', 'Email Marketing'],
        'good_to_have': ['Paid Ads', 'CRM Tools', 'Video Marketing', 'Marketing Automation']
    }
}

def call_openai(messages, max_tokens=800):
    api_key = current_app.config.get('OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content
    except Exception as e:
        print("OPENAI ERROR:", e)
        return None

    
    

@ai_bp.route('/chatbot')
@login_required
def chatbot():
    history = current_user.chat_messages.order_by(ChatMessage.created_at.desc()).limit(20).all()
    return render_template('chatbot.html', history=list(reversed(history)))

@ai_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    # Build context
    user_context = f"User: {current_user.name}, Target roles: {', '.join(current_user.get_target_roles())}, Skills: {', '.join(current_user.get_skills()[:8])}"

    system_prompt = f"""You are Preptra's AI Career Advisor — an expert in campus placements, technical interviews, and career development for Indian engineering students. You are friendly, direct, and highly knowledgeable.

User context: {user_context}

Provide structured, actionable advice. Use emojis occasionally. Keep responses concise but complete. For roadmaps and study plans, use bullet points. Focus on practical tips."""

    # Try AI
    response = call_openai([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ], max_tokens=600)

    if not response:
        # Fallback rule-based
        response = get_fallback_response(message)

    # Save to DB
    msg = ChatMessage(user_id=current_user.id, message=message, response=response)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'response': response})

def get_fallback_response(message):
    msg = message.lower()
    if any(w in msg for w in ['resume', 'cv']):
        return "📄 **Resume Tips:**\n• Keep it 1 page for freshers\n• Use action verbs: Led, Built, Reduced, Increased\n• Quantify achievements (e.g., 'Improved performance by 30%')\n• Include: Education, Projects, Skills, Certifications, Internships\n• Use ATS-friendly format — avoid tables/graphics"
    if any(w in msg for w in ['dsa', 'data structure', 'algorithm', 'leetcode']):
        return "💻 **DSA Preparation Roadmap:**\n• Arrays & Strings (1 week)\n• Linked Lists, Stacks, Queues (1 week)\n• Trees & Graphs (2 weeks)\n• Dynamic Programming (2 weeks)\n• Practice: LeetCode Top 150, Striver's SDE Sheet\n• Daily: 2-3 problems minimum"
    if any(w in msg for w in ['interview', 'hr', 'technical']):
        return "🎯 **Interview Preparation:**\n• Technical: Revise DSA, OS, DBMS, Networks, OOP\n• HR: Prepare STAR format stories for behavioral questions\n• Practice mock interviews with Preptra's Mock module\n• Research the company beforehand\n• Prepare 5+ smart questions to ask the interviewer"
    if any(w in msg for w in ['placement', 'campus', 'prepare']):
        return "🚀 **Campus Placement Strategy:**\n• Build a strong resume with 2-3 solid projects\n• Master DSA — minimum 100 LeetCode problems\n• Apply to 15-20 companies for better odds\n• Network: LinkedIn profile + college alumni connections\n• Track applications in Preptra — analyze your weak rounds\n• Mock interviews: Practice at least 10 before placements start"
    return "👋 Hi! I'm your Preptra AI Career Advisor. I can help with:\n• Interview preparation strategies\n• Resume and skill gap analysis\n• Company-specific preparation\n• Study plans and roadmaps\n• Career guidance\n\nWhat would you like to know? (Add your OpenAI API key in .env for enhanced AI responses)"

@ai_bp.route('/skill-gap')
@login_required
def skill_gap():
    return render_template('skill_gap.html', skill_map=SKILL_MAP)

@ai_bp.route('/api/skill-gap', methods=['POST'])
@login_required
def analyze_skill_gap():
    data = request.get_json()
    target_role = data.get('role', 'Software Developer')
    user_skills = [s.lower().strip() for s in current_user.get_skills()]

    role_data = SKILL_MAP.get(target_role, SKILL_MAP['Software Developer'])
    required = role_data['required']
    good_to_have = role_data['good_to_have']

    have = []
    missing = []
    for skill in required:
        found = any(us in skill.lower() or skill.lower() in us for us in user_skills)
        if found: have.append(skill)
        else: missing.append(skill)

    coverage = round(len(have) / max(len(required), 1) * 100, 1)

    # Generate roadmap
    roadmap = []
    for i, skill in enumerate(missing[:6]):
        resources = {
            'SQL': 'SQLZoo.net, Mode Analytics Tutorial',
            'Python': 'Python.org, Automate the Boring Stuff',
            'Data Structures': 'GeeksforGeeks DSA, LeetCode',
            'Algorithms': 'Striver SDE Sheet, CLRS Book',
            'React/Angular': 'official docs, FreeCodeCamp',
            'Docker': 'Docker official getting-started',
            'AWS/GCP': 'AWS Free Tier tutorials, Cloud Guru',
            'Machine Learning': 'Kaggle Learn, Andrew Ng Course',
        }
        res = next((v for k, v in resources.items() if k.lower() in skill.lower()), 'Coursera / YouTube / Official Docs')
        roadmap.append({
            'skill': skill,
            'priority': 'High' if i < 3 else 'Medium',
            'estimated_weeks': 2 if i < 3 else 3,
            'resources': res
        })

    # Try AI enhancement
    ai_analysis = call_openai([{
        "role": "user",
        "content": f"For a {target_role} role, the candidate has: {', '.join(have)}. They're missing: {', '.join(missing[:5])}. Give 3-4 specific, actionable tips to bridge the gap in 2-3 sentences each. Be direct and practical."
    }], max_tokens=400)

    return jsonify({
        'have': have,
        'missing': missing,
        'coverage': coverage,
        'roadmap': roadmap,
        'ai_tips': ai_analysis or f"Focus on the top missing skills: {', '.join(missing[:3])}. Start with free resources and build projects to demonstrate proficiency.",
        'good_to_have': good_to_have
    })

@ai_bp.route('/resume-analyzer')
@login_required
def resume_analyzer():
    return render_template('resume_analyzer.html')

@ai_bp.route('/api/analyze-resume', methods=['POST'])
@login_required
def analyze_resume():
    resume_text = ''
    if 'file' in request.files:
        file = request.files['file']
        if file.filename.endswith('.pdf'):
            try:
                import PyPDF2, io
                reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                resume_text = ' '.join(page.extract_text() or '' for page in reader.pages)
            except: resume_text = ''
        elif file.filename.endswith('.txt'):
            resume_text = file.read().decode('utf-8', errors='ignore')
    else:
        resume_text = request.form.get('resume_text', '')

    if not resume_text.strip():
        return jsonify({'error': 'Could not read resume. Please paste the text.'}), 400

    current_user.resume_text = resume_text[:5000]
    db.session.commit()

    # Rule-based analysis
    text_lower = resume_text.lower()
    score = 50  # Base score
    issues = []
    strengths = []
    suggestions = []

    # Check sections
    sections = {'education': 10, 'project': 8, 'skill': 8, 'experience': 10, 'certif': 5, 'internship': 8}
    for sec, pts in sections.items():
        if sec in text_lower:
            score += pts; strengths.append(f"Contains {sec.title()} section")
        else:
            issues.append(f"Missing {sec.title()} section")

    # Check keywords
    action_verbs = ['developed', 'built', 'designed', 'implemented', 'improved', 'led', 'created', 'managed', 'deployed']
    found_verbs = [v for v in action_verbs if v in text_lower]
    if len(found_verbs) >= 4: score += 5; strengths.append(f"Good use of action verbs ({', '.join(found_verbs[:3])}...)")
    else: issues.append("Use more action verbs (e.g., Built, Designed, Led, Deployed)")

    # Quantification check
    import re
    numbers = re.findall(r'\d+%|\d+x|\$\d+|\d+ (users|students|team|projects)', resume_text)
    if numbers: score += 5; strengths.append("Good quantification of achievements")
    else: suggestions.append("Quantify your impact: 'Improved performance by 30%', 'Built for 500+ users'")

    # Length check
    word_count = len(resume_text.split())
    if 300 <= word_count <= 700: score += 5; strengths.append("Optimal resume length")
    elif word_count < 200: issues.append("Resume seems too short. Add more detail.")
    elif word_count > 900: issues.append("Resume may be too long. Keep to 1 page for freshers.")

    score = min(score, 100)

    # Add standard suggestions
    suggestions += [
        "Tailor keywords to each job description for ATS optimization",
        "Add LinkedIn profile URL and GitHub link",
        "List projects with: tech stack, problem solved, results achieved",
        "Keep consistent formatting — same font, bullet style throughout"
    ]

    # Try AI for detailed feedback
    ai_feedback = call_openai([{
        "role": "system",
        "content": "You are an expert resume reviewer for campus placements in India. Analyze the resume and provide 3-4 specific, actionable improvements. Be direct and constructive."
    }, {
        "role": "user",
        "content": f"Resume text:\n{resume_text[:2000]}\n\nProvide specific feedback on: 1) Content quality 2) Missing sections 3) Improvements with examples"
    }], max_tokens=500)

    return jsonify({
        'score': score,
        'strengths': strengths,
        'issues': issues,
        'suggestions': suggestions,
        'ai_feedback': ai_feedback or "Great start! Focus on quantifying achievements and adding strong action verbs to stand out.",
        'word_count': word_count
    })

@ai_bp.route('/study-plan')
@login_required
def study_plan():
    plans = current_user.study_plans.order_by(StudyPlan.created_at.desc()).limit(5).all()
    return render_template('study_plan.html', plans=plans)

@ai_bp.route('/api/generate-plan', methods=['POST'])
@login_required
def generate_study_plan():
    data = request.get_json()
    target_role = data.get('role', 'Software Developer')
    days_left = int(data.get('days', 30))
    weak_areas = data.get('weak_areas', [])
    goal = data.get('goal', 'Get placed at a top company')

    # Rule-based plan generator
    weeks = max(1, days_left // 7)

    base_plans = {
        'Software Developer': [
            {'week': 1, 'focus': 'Arrays, Strings, Basic Algorithms', 'daily': '2h DSA + 30min theory', 'resources': 'LeetCode Easy, GFG'},
            {'week': 2, 'focus': 'Linked Lists, Stacks, Queues, Recursion', 'daily': '2h DSA + 1h projects', 'resources': 'LeetCode Medium'},
            {'week': 3, 'focus': 'Trees, Graphs, BFS/DFS', 'daily': '2.5h DSA + 30min OS/DBMS', 'resources': 'Striver Sheet'},
            {'week': 4, 'focus': 'Dynamic Programming, Mock Interviews', 'daily': '2h DP + 1h interview prep', 'resources': 'LeetCode DP playlist'},
        ],
        'Data Analyst': [
            {'week': 1, 'focus': 'SQL Fundamentals, Excel', 'daily': '2h SQL practice + 1h Excel', 'resources': 'SQLZoo, Mode SQL'},
            {'week': 2, 'focus': 'Python - Pandas, NumPy', 'daily': '2.5h Python + mini projects', 'resources': 'Kaggle Learn Python'},
            {'week': 3, 'focus': 'Data Visualization, Tableau/Power BI', 'daily': '2h visualization practice', 'resources': 'Tableau Public'},
            {'week': 4, 'focus': 'Statistics, Case Studies, Mock Interviews', 'daily': '1.5h stats + 1h cases', 'resources': 'StatQuest YouTube'},
        ]
    }

    plan_weeks = base_plans.get(target_role, base_plans['Software Developer'])
    # Trim to actual weeks available
    plan_weeks = plan_weeks[:min(weeks, len(plan_weeks))]

    # Add weak area focus
    if weak_areas:
        plan_weeks.append({
            'week': len(plan_weeks)+1,
            'focus': f"Targeted Practice: {', '.join(weak_areas[:3])}",
            'daily': '3h focused practice on weak areas',
            'resources': 'Refer to Preptra Resource Hub'
        })

    # Try AI enhancement
    ai_plan_text = call_openai([{
        "role": "system",
        "content": "You are an expert career coach for Indian engineering students. Create a practical, day-wise study plan."
    }, {
        "role": "user",
        "content": f"Create a {days_left}-day study plan for someone targeting {target_role} role. Weak areas: {', '.join(weak_areas) if weak_areas else 'None specified'}. Goal: {goal}. Give a week-by-week breakdown with specific daily tasks, time allocation, and resources. Be specific and actionable."
    }], max_tokens=700)

    plan_content = {
        'weeks': plan_weeks,
        'ai_plan': ai_plan_text,
        'daily_schedule': {
            'morning': '6:00-8:00 AM — DSA / Core subject study',
            'afternoon': '2:00-4:00 PM — Project work / Practice problems',
            'evening': '8:00-9:30 PM — Revision + Mock test + Notes'
        },
        'milestones': [
            f"Week 1: Complete fundamentals, solve 20+ problems",
            f"Week {max(1, weeks//2)}: Solve 60+ problems, complete 1 project",
            f"Final week: Mock interviews daily, revision, applications"
        ]
    }

    study_plan = StudyPlan(
        user_id=current_user.id,
        title=f"{target_role} — {days_left} Day Plan",
        target_role=target_role,
        days_left=days_left,
        weak_areas=json.dumps(weak_areas),
        plan_content=json.dumps(plan_content)
    )
    db.session.add(study_plan)
    db.session.commit()

    return jsonify({'plan': plan_content, 'plan_id': study_plan.id})
