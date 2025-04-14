from app import db
from datetime import datetime

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)       
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    rental_type = db.Column(db.String(20), default='daily')
    damage_charge = db.Column(db.Float, default=0.0)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), index=True)

    # Relationships
    user = db.relationship('User', back_populates='reservations')
    car = db.relationship('Car', back_populates='reservations')
    payment = db.relationship('Payment', back_populates='reservation', uselist=False)
    damage_reports = db.relationship('DamageReport', back_populates='reservation')

    VALID_STATUSES = ['pending', 'confirmed', 'cancelled', 'completed']
    def __init__(self, **kwargs):
        if kwargs.get('status') not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of {self.VALID_STATUSES}")
        super().__init__(**kwargs)

    @classmethod
    def calculate_price(cls, car, start_date, end_date, rental_type='daily'):
        days = (end_date - start_date).days
        if rental_type == 'monthly':
            return (car.price_per_day * 30) * 0.9
        elif rental_type == 'yearly':
            return (car.price_per_day * 365) * 0.8
        return days * car.price_per_day

    def __repr__(self):
        return f'<Reservation {self.id} for Car {self.car_id} by User {self.user_id}>'