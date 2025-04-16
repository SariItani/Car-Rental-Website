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
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-key'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_IDENTITY_CLAIM = 'identity'

    # Flask configuration
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
