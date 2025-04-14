from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Changed to nullable=False
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    type = db.Column(db.String(20), nullable=False)  # Changed to nullable=False
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }
    
    # Relationships
    reservations = db.relationship('Reservation', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "type": self.type,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "driving_license": getattr(self, 'driving_license', None),
            "perms": getattr(self, 'perms', None)
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
    
class Admin(User):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    perms = db.Column(db.String(100))
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }
    
    def __init__(self, **kwargs):
        kwargs['role'] = 'admin'  # Ensure role is always set
        super().__init__(**kwargs)

class Client(User):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    driving_license = db.Column(db.String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'client',
    }
    
    def __init__(self, **kwargs):
        kwargs['role'] = 'client'  # Ensure role is always set
        super().__init__(**kwargs)
