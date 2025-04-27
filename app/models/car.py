from app import db
from datetime import datetime

from app.models.favorite import Favorite
from app.models.reservation import Reservation

class Car(db.Model):
    __tablename__ = 'cars'
    
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False, index=True)
    model = db.Column(db.String(50), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available', index=True)
    vehicle_type = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(50), default='city', nullable=False)
    category = db.Column(db.String(20), default='medium')  # small/medium/large
    
    # Relationships
    reservations = db.relationship('Reservation', back_populates='car', cascade='all, delete-orphan')
    insurances = db.relationship('Insurance', back_populates='car', cascade='all, delete-orphan')

    VALID_TYPES = ['sedan', 'suv', '4x4', 'luxury']
    VALID_LOCATIONS = ['city', 'mountains', 'desert', 'snow']

    def __init__(self, **kwargs):
        if kwargs.get('vehicle_type') not in self.VALID_TYPES:
            raise ValueError(f"Invalid vehicle type. Must be one of {self.VALID_TYPES}")
        if kwargs.get('location') not in self.VALID_LOCATIONS:
            raise ValueError(f"Invalid location. Must be one of {self.VALID_LOCATIONS}")
        kwargs['category'] = self.infer_category(kwargs.get('vehicle_type'))
        super().__init__(**kwargs)
    
    def is_available(self, start_date, end_date):
        """Check if car is available for given dates"""
        overlapping = Reservation.query.filter(
            Reservation.car_id == self.id,
            Reservation.end_date >= start_date,
            Reservation.start_date <= end_date,
            Reservation.status != 'cancelled'
        ).first()
        return not overlapping and self.status == 'available'
    
    def update_status_based_on_reservations(self):
        """Update car status based on active reservations"""
        active_reservation = Reservation.query.filter(
            Reservation.car_id == self.id,
            Reservation.end_date >= datetime.now().date(),
            Reservation.status.in_(['confirmed', 'pending'])
        ).first()
        
        self.status = 'reserved' if active_reservation else 'available'

    def to_dict(self, user_id=None):
        """Convert car object to dictionary"""
        data = {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'price_per_day': float(self.price_per_day),
            'status': self.status,
            'vehicle_type': self.vehicle_type,
            'location': self.location
        }
        if user_id:
            data['is_favorited'] = Favorite.query.filter_by(
                user_id=user_id, car_id=self.id
            ).first() is not None
        return data
    
    @classmethod
    def get_by_terrain(cls, location):
        if location == 'mountains':
            return cls.query.filter(cls.vehicle_type.in_(['suv', '4x4']))
        elif location == 'desert':
            return cls.query.filter_by(vehicle_type='4x4')
        elif location == 'snow':
            return cls.query.filter(cls.vehicle_type.in_(['suv', '4x4']))
        else:  # city
            return cls.query.filter_by(vehicle_type='sedan')
        
    @classmethod
    def infer_category(cls, vehicle_type):
        """Infer category based on vehicle type"""
        if vehicle_type in ['sedan', 'suv']:
            return 'medium'
        elif vehicle_type == '4x4':
            return 'large'
        else:
            return 'small'
    
    def __repr__(self):
        return f'<Car {self.make} {self.model} ({self.year})>'