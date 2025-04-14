from app import db
from datetime import datetime

class DamageReport(db.Model):
    __tablename__ = 'damage_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    repair_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='reported')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    
    # Relationship
    reservation = db.relationship('Reservation', back_populates='damage_reports')

    def __repr__(self):
        return f'<DamageReport {self.id} for Reservation {self.reservation_id}>'