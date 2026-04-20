from flask_login import LoginManager
from flask_mail import Mail
from models import db, User
import os
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # simple version best hai
from flask import Flask
from config import Config

mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access Preptra.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        return {'now': lambda: datetime.utcnow()}

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.tracker import tracker_bp
    from routes.ai_features import ai_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tracker_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        # Create default admin
        if not User.query.filter_by(email='admin@preptra.com').first():
            admin = User(name='Admin', email='admin@preptra.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
