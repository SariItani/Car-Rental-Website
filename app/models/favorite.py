from app import db
from datetime import datetime

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='favorites')
    car = db.relationship('Car', backref='favorited_by')

    def to_dict(self):
        return {
            'id': self.id,
            'car_id': self.car_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }