from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime
import requests
import json
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        college = request.form.get('college', '').strip()
        course = request.form.get('course', '').strip()
        grad_year = request.form.get('graduation_year', '')

        if not name or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return render_template('auth/register.html')

        user = User(
            name=name, email=email, college=college, course=course,
            graduation_year=int(grad_year) if grad_year else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to Preptra, {name}! Let\'s build your career.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always show success to prevent email enumeration
        flash('If that email is registered, you will receive reset instructions shortly.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Google OAuth
@auth_bp.route('/auth/google')
def google_login():
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    if not google_client_id:
        flash('Google login is not configured. Please use email/password.', 'error')
        return redirect(url_for('auth.login'))

    try:
        discovery = requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()
        auth_endpoint = discovery['authorization_endpoint']
        redirect_uri = url_for('auth.google_callback', _external=True)
        params = {
            'client_id': google_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
        }
        import urllib.parse
        auth_url = auth_endpoint + '?' + urllib.parse.urlencode(params)
        return redirect(auth_url)
    except Exception as e:
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        flash('Google login failed.', 'error')
        return redirect(url_for('auth.login'))
    try:
        discovery = requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()
        token_endpoint = discovery['token_endpoint']
        redirect_uri = url_for('auth.google_callback', _external=True)
        token_response = requests.post(token_endpoint, data={
            'code': code,
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        })
        token_data = token_response.json()
        access_token = token_data.get('access_token')

        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        userinfo = userinfo_response.json()
        google_id = userinfo.get('id')
        email = userinfo.get('email', '').lower()
        name = userinfo.get('name', '')
        picture = userinfo.get('picture', '')

        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, google_id=google_id, avatar_url=picture)
            db.session.add(user)
        else:
            user.google_id = google_id
            user.avatar_url = picture
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash('Google login failed. Please use email/password.', 'error')
        return redirect(url_for('auth.login'))

# Profile update API
@auth_bp.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    if data.get('name'): current_user.name = data['name']
    if data.get('college'): current_user.college = data['college']
    if data.get('course'): current_user.course = data['course']
    if data.get('graduation_year'): current_user.graduation_year = data['graduation_year']
    if 'target_roles' in data: current_user.target_roles = json.dumps(data['target_roles'])
    if 'skills' in data: current_user.skills = json.dumps(data['skills'])
    if 'certifications' in data: current_user.certifications = json.dumps(data['certifications'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated!'})
