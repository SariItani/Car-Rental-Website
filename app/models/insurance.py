# models/insurance.py
from app import db
from datetime import datetime, timedelta

class Insurance(db.Model):
    __tablename__ = 'insurances'
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'basic', 'premium', 'full'
    expiry_date = db.Column(db.Date, nullable=False)
    coverage_amount = db.Column(db.Float, nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'))
    
    car = db.relationship('Car', back_populates='insurances')

    def __repr__(self):
        return f'<Insurance {self.provider} ({self.type}) for Car {self.car_id}>'
