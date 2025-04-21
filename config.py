from datetime import timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

current_file_path = Path(__file__).absolute()
project_root = current_file_path.parent
while not (project_root / 'run.py').exists() and project_root != project_root.parent:
    project_root = project_root.parent

if not (project_root / 'run.py').exists():
    raise RuntimeError("Could not locate project root directory!")

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rental.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration - Dual Mode (Headers for API, Cookies for Frontend)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-key'
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Cookie-specific settings
    JWT_COOKIE_SECURE = True  # HTTPS in production
    JWT_COOKIE_CSRF_PROTECT = True  # Enable CSRF protection for cookies
    JWT_CSRF_IN_COOKIES = True  # Store CSRF token in separate cookie
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
    JWT_COOKIE_DOMAIN = None  # Set if you need cross-subdomain cookies
    JWT_SESSION_COOKIE = False  # False = cookie expires when browser closes
    
    # Token expiration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_IDENTITY_CLAIM = 'identity'
    
    # CSRF Protection (for forms)
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = os.environ.get('CSRF_SESSION_KEY') or 'another-super-secret-key'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'yet-another-secret-key'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # CORS (for API)
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = ['Authorization']

    # Flask configuration
    SECRET_KEY=os.environ.get('JWT_SECRET_KEY') or 'a-super-secret-key'
    EXPLAIN_TEMPLATE_LOADING = True
    TEMPLATES_AUTO_RELOAD = True
    PROJECT_ROOT = project_root
    TEMPLATES_FOLDER = str(PROJECT_ROOT / 'templates')
    STATIC_FOLDER = str(PROJECT_ROOT / 'static')
    API_BASE_URL = 'http://localhost:5000/api'
    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_DEBUG_TB_INTERCEPT_REDIRECTS = False
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for development

    # Language and localization
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_SUPPORTED_LOCALES = ['en', 'fr', 'ar']

    @classmethod
    def get_template_folder(cls):
        return cls.TEMPLATES_FOLDER
        
    @classmethod
    def get_static_folder(cls):
        return cls.STATIC_FOLDER

# class ProductionConfig(Config):
#     STATIC_URL = 'https://your-cdn.example.com/static'  # If using CDN
#     TEMPLATES_AUTO_RELOAD = False  # For better performance
