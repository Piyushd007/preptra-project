from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Application, Round
from datetime import datetime

tracker_bp = Blueprint('tracker', __name__)

@tracker_bp.route('/tracker')
@login_required
def tracker():
    apps = current_user.applications.order_by(Application.created_at.desc()).all()
    return render_template('tracker.html', applications=apps)

@tracker_bp.route('/api/application', methods=['POST'])
@login_required
def add_application():
    data = request.get_json()
    try:
        app = Application(
            user_id=current_user.id,
            company=data['company'],
            role=data['role'],
            package_lpa=float(data.get('package_lpa') or 0),
            location=data.get('location', ''),
            status=data.get('status', 'Applied'),
            notes=data.get('notes', ''),
            job_link=data.get('job_link', ''),
        )
        if data.get('applied_date'):
            app.applied_date = datetime.strptime(data['applied_date'], '%Y-%m-%d').date()
        db.session.add(app)
        db.session.flush()

        # Add rounds
        for i, r in enumerate(data.get('rounds', [])):
            rd = Round(
                application_id=app.id,
                round_type=r.get('type', 'Technical'),
                status=r.get('status', 'Pending'),
                notes=r.get('notes', ''),
                order_num=i+1
            )
            if r.get('date'):
                rd.round_date = datetime.strptime(r['date'], '%Y-%m-%d').date()
            db.session.add(rd)

        db.session.commit()
        return jsonify({'success': True, 'id': app.id, 'message': 'Application added!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@tracker_bp.route('/api/application/<int:app_id>', methods=['GET'])
@login_required
def get_application(app_id):
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first_or_404()
    return jsonify(app.to_dict())

@tracker_bp.route('/api/application/<int:app_id>', methods=['PUT'])
@login_required
def update_application(app_id):
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    try:
        if 'company' in data: app.company = data['company']
        if 'role' in data: app.role = data['role']
        if 'package_lpa' in data: app.package_lpa = float(data['package_lpa'] or 0)
        if 'location' in data: app.location = data['location']
        if 'status' in data: app.status = data['status']
        if 'notes' in data: app.notes = data['notes']
        if 'job_link' in data: app.job_link = data['job_link']
        if data.get('applied_date'):
            app.applied_date = datetime.strptime(data['applied_date'], '%Y-%m-%d').date()

        # Update rounds
        if 'rounds' in data:
            for r in app.rounds: db.session.delete(r)
            for i, r in enumerate(data['rounds']):
                rd = Round(
                    application_id=app.id,
                    round_type=r.get('type', 'Technical'),
                    status=r.get('status', 'Pending'),
                    notes=r.get('notes', ''),
                    order_num=i+1
                )
                if r.get('date'):
                    rd.round_date = datetime.strptime(r['date'], '%Y-%m-%d').date()
                db.session.add(rd)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Application updated!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@tracker_bp.route('/api/application/<int:app_id>', methods=['DELETE'])
@login_required
def delete_application(app_id):
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first_or_404()
    db.session.delete(app)
    db.session.commit()
    return jsonify({'success': True})

@tracker_bp.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    apps = current_user.applications.order_by(Application.created_at.desc()).all()
    return jsonify([a.to_dict() for a in apps])
