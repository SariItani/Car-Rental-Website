from pathlib import Path
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
from flask_babel import Babel
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
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
    app.config.setdefault('WTF_CSRF_CHECK_DEFAULT', False)
    csrf._exempt_views.add('api.')
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'frontend_auth.login'
    migrate.init_app(app, db)
            
    # Add user loader
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.api.auth import bp as auth_bp
    from app.routes.api.cars import bp as cars_bp
    from app.routes.api.admin import bp as admin_bp
    from app.routes.api.payments import bp as payments_bp
    from app.routes.api.favorites import bp as favorites_bp
    from app.routes.api.refund import bp as refund_bp

    from app.routes.frontend.main import bp as main_bp
    from app.routes.frontend.cars import bp as frontend_cars_bp
    from app.routes.frontend.auth import bp as frontend_auth_bp
    from app.routes.frontend.dashboard import bp as dashboard_bp

    app.register_blueprint(dashboard_bp, url_prefix='/dashboard', template_folder='../templates')
    app.register_blueprint(main_bp, url_prefix='/', template_folder='../templates')
    app.register_blueprint(frontend_cars_bp, template_folder='../templates')
    app.register_blueprint(frontend_auth_bp, template_folder='../templates')
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(refund_bp, url_prefix='/api/refunds')
    app.register_blueprint(favorites_bp, url_prefix='/api/favorites')
    app.register_blueprint(cars_bp, url_prefix='/api/cars')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    
    return app

from app.models import user, car, reservation, payment, insurance, damage