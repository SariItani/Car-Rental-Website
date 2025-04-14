from app import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    
    # Relationship
    reservation = db.relationship('Reservation', back_populates='payment')

    VALID_METHODS = ['credit_card', 'debit_card', 'bank_transfer']
    VALID_STATUSES = ['pending', 'completed', 'failed', 'refunded']

    def __init__(self, **kwargs):
        if kwargs.get('method') not in self.VALID_METHODS:
            raise ValueError(f"Invalid payment method. Must be one of {self.VALID_METHODS}")
        if kwargs.get('status') not in self.VALID_STATUSES:
            raise ValueError(f"Invalid payment status. Must be one of {self.VALID_STATUSES}")
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Payment {self.id} for Reservation {self.reservation_id}>'