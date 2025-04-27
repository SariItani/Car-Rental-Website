from datetime import datetime
from app import db

class Refund(db.Model):
    __tablename__ = 'refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    # Relationships
    reservation = db.relationship('Reservation', backref='refunds')

    def to_dict(self):
        return {
            "id": self.id,
            "reservation_id": self.reservation_id,
            "amount": self.amount,
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }