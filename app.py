from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models and routes
from app.models import user, car, reservation
from app.routes import auth, cars, admin

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(cars.bp)
app.register_blueprint(admin.bp)

if __name__ == '__main__':
    app.run()