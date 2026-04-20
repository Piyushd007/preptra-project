from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    total_apps = Application.query.count()
    return render_template('admin.html', users=users, total_apps=total_apps)

@admin_bp.route('/api/admin/users')
@login_required
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id, 'name': u.name, 'email': u.email,
        'college': u.college, 'apps': u.applications.count(),
        'created': u.created_at.strftime('%d %b %Y') if u.created_at else ''
    } for u in users])
