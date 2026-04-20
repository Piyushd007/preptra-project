# ⚡ Preptra — AI-Powered Placement Preparation System

**A full-stack web application for campus placement preparation with AI-powered tools.**

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

---

### Step 1: Install Python
Download from https://python.org/downloads — make sure to check **"Add to PATH"** during install.

---

### Step 2: Set Up the Project

Open a terminal/command prompt and run:

```bash
# Navigate to the preptra folder
cd preptra

# Create a virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

### Step 3: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings (see Configuration section below)
```

At minimum, the app runs **without any API keys** — AI features will use built-in fallback responses.

---

### Step 4: Run the App

```bash
python app.py
```

Open your browser and go to: **http://localhost:5000**

---

## 🔑 Default Admin Account
- **Email:** admin@preptra.com
- **Password:** admin123

Create your own account via the Register page for best experience.

---

## ⚙️ Configuration

Edit the `.env` file:

### OpenAI API Key (for full AI features)
1. Go to https://platform.openai.com/api-keys
2. Create a new key
3. Add to `.env`: `OPENAI_API_KEY=sk-your-key-here`

Without this key, the app uses built-in rule-based responses for all AI features.

### Google OAuth (for "Login with Google")
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Go to **APIs & Services → Credentials**
4. Create **OAuth 2.0 Client ID** → Web Application
5. Add authorized redirect URI: `http://localhost:5000/auth/google/callback`
6. Copy Client ID and Secret to `.env`

---

## 📁 Project Structure

```
preptra/
├── app.py              — Main Flask app entry point
├── config.py           — Configuration settings
├── models.py           — Database models (SQLite)
├── requirements.txt    — Python dependencies
├── .env.example        — Environment variables template
├── routes/
│   ├── auth.py         — Login, Register, Google OAuth
│   ├── main.py         — Dashboard, Analytics, Readiness Score, Mock Interview
│   ├── tracker.py      — Application Tracker CRUD
│   ├── ai_features.py  — Chatbot, Skill Gap, Resume Analyzer, Study Plan
│   └── admin.py        — Admin Panel
├── templates/
│   ├── base.html       — Shared layout with sidebar navigation
│   ├── auth/           — Login, Register, Forgot Password pages
│   ├── dashboard.html  — Main dashboard
│   ├── tracker.html    — Application tracker
│   ├── analytics.html  — Analytics with charts
│   ├── readiness_score.html — Placement Readiness Score
│   ├── chatbot.html    — AI Career Chatbot
│   ├── skill_gap.html  — Skill Gap Analyzer
│   ├── resume_analyzer.html — AI Resume Analyzer
│   ├── study_plan.html — Study Plan Generator
│   ├── mock_interview.html  — Mock Interview Studio
│   ├── resources.html  — Resource Hub
│   ├── profile.html    — User Profile
│   └── admin.html      — Admin Panel
└── static/
    ├── css/style.css   — Complete CSS stylesheet
    └── js/main.js      — JavaScript utilities
```

---

## 🎯 Features

| Module | Description |
|--------|-------------|
| 🔐 Authentication | Email/Password + Google OAuth + Forgot Password |
| 📊 Dashboard | Stats overview, readiness gauge, recent applications |
| 📋 Application Tracker | Log companies, roles, packages, round-wise status |
| 📈 Analytics | Charts for status, round failures, monthly trends |
| ⚡ Readiness Score | Proprietary algorithm (skills 30% + certs 20% + mocks 15% + resume 15% + interviews 10% + consistency 10%) |
| 🤖 AI Chatbot | Career advisor powered by OpenAI GPT-3.5 |
| 🎯 Skill Gap Analyzer | Role-specific skill benchmarking with learning roadmap |
| 📄 Resume Analyzer | Score your resume + ATS tips + AI feedback |
| 📅 Study Plan Generator | Day-wise personalized preparation roadmap |
| 🎤 Mock Interview Studio | Timer-based Q&A with AI feedback and self-rating |
| 📚 Resource Hub | Curated guides, certifications, YouTube channels |
| 👤 Profile | Manage skills, certifications, target roles |
| 🛡️ Admin Panel | User management and platform analytics |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Database:** SQLite (zero-config, runs anywhere)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Charts:** Chart.js
- **UI Framework:** Bootstrap 5 + Custom CSS
- **AI:** OpenAI GPT-3.5 Turbo (with rule-based fallback)
- **Auth:** Flask-Login, Google OAuth 2.0
- **Icons:** Bootstrap Icons

---

## 🔧 Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**Port already in use:**
```bash
python app.py  # or change port in app.py: port=5001
```

**Database issues:**
```bash
# Delete the database and restart (this resets all data)
del preptra.db   # Windows
rm preptra.db    # Mac/Linux
python app.py
```

**Google login not working:**
- Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`
- Verify redirect URI `http://localhost:5000/auth/google/callback` is added in Google Console

---

## 📝 Notes for Major Project Submission

- Built with Agile methodology (iterative sprints)
- Database normalized and uses SQLAlchemy ORM
- RESTful API architecture
- AI integration with OpenAI GPT-3.5 + rule-based fallback
- Responsive design (mobile-friendly)
- Handles 1000+ users via Flask (scalable to Nginx + Gunicorn for production)
- Admin panel for institutional management

---

*Developed as Final Year Major Project — BCA 6th Sem*
*Preptra: AI-Powered Placement Preparation and Career Intelligence System*
