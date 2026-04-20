import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'preptra-secret-key-change-in-production-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'preptra.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or ''
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or ''
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
