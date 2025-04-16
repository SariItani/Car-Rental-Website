from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
# from flask_bootstrap import Bootstrap
from flask_babel import Babel
from flask_login import LoginManager
from flask_caching import Cache

babel = Babel()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

def create_app(config_class=Config):
    app = Flask(__name__,
        template_folder=config_class.TEMPLATES_FOLDER,
        static_folder=config_class.STATIC_FOLDER
    )
    app.config.from_object(config_class)
    
    # Initialize extensions
    cache.init_app(app)
    # Bootstrap(app)
    babel.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.api.auth import bp as auth_bp
    from app.routes.api.cars import bp as cars_bp
    from app.routes.api.admin import bp as admin_bp
    from app.routes.api.payments import bp as payments_bp
    from app.routes.frontend.main import bp as main_bp
    from app.routes.frontend.cars import bp as frontend_cars_bp

    app.register_blueprint(main_bp, url_prefix='/', template_folder='../templates')
    app.register_blueprint(frontend_cars_bp, template_folder='../templates')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cars_bp, url_prefix='/api/cars')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    
    return app

from app.models import user, car, reservation, payment, insurance, damage