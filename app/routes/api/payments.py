from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Payment, Reservation, Car
from datetime import datetime
from sqlalchemy.orm import joinedload

bp = Blueprint('payments', __name__)

@bp.route('/reservations', methods=['GET'])
@jwt_required()
def user_reservations():
    """Get all reservations for the current user with payment status"""
    user_id = get_jwt_identity()
    
    reservations = Reservation.query.options(
        joinedload(Reservation.car),
        joinedload(Reservation.payment)
    ).filter_by(
        user_id=user_id
    ).order_by(
        Reservation.start_date.desc()
    ).all()
    
    return jsonify([{
        'id': r.id,
        'car': {
            'id': r.car.id,
            'make': r.car.make,
            'model': r.car.model,
            'year': r.car.year
        },
        'dates': {
            'start': r.start_date.isoformat(),
            'end': r.end_date.isoformat()
        },
        'total_price': r.total_price,
        'status': r.status,
        'payment': {
            'status': r.payment.status if r.payment else None,
            'amount': r.payment.amount if r.payment else None,
            'date': r.payment.payment_date.isoformat() if r.payment and r.payment.payment_date else None
        } if r.payment else None,
        'damage_charge': r.damage_charge
    } for r in reservations])

@bp.route('/history', methods=['GET'])
@jwt_required()
def payment_history():
    """Get payment history for the current user"""
    user_id = get_jwt_identity()
    
    payments = Payment.query.join(
        Reservation
    ).filter(
        Reservation.user_id == user_id
    ).order_by(
        Payment.payment_date.desc()
    ).all()
    
    return jsonify([{
        'id': p.id,
        'amount': p.amount,
        'status': p.status,
        'method': p.method,
        'date': p.payment_date.isoformat(),
        'reservation_id': p.reservation_id,
        'car': {
            'make': p.reservation.car.make,
            'model': p.reservation.car.model
        } if p.reservation and p.reservation.car else None
    } for p in payments])

@bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No payment data provided"}), 400
    
    if 'reservation_id' not in data:
        return jsonify({
            "error": "Missing reservation_id",
            "required_fields": ["reservation_id", "method (optional)"]
        }), 400
    
    user_id = get_jwt_identity()
    
    # Get reservation with all related data
    reservation = Reservation.query.options(
        joinedload(Reservation.car),
        joinedload(Reservation.payment)
    ).filter_by(
        id=data['reservation_id'],
        user_id=user_id
    ).first()
    
    if not reservation:
        return jsonify({
            "error": "Reservation not found",
            "message": "Either the reservation doesn't exist or doesn't belong to you",
            "reservation_id": data['reservation_id'],
            "user_id": user_id
        }), 404
    
    if reservation.status == 'cancelled':
        return jsonify({
            "error": "Reservation cancelled",
            "message": "Cannot process payment for cancelled reservation",
            "reservation_status": reservation.status
        }), 400
    
    if reservation.payment and reservation.payment.status == 'completed':
        return jsonify({
            "error": "Payment already completed",
            "message": "This reservation has already been paid for",
            "payment_id": reservation.payment.id,
            "payment_date": reservation.payment.payment_date.isoformat()
        }), 400
    
    try:
        payment = Payment(
            amount=reservation.total_price,
            status='completed',
            method=data.get('method', 'credit_card'),
            payment_date=datetime.utcnow(),
            transaction_id=f"txn_{datetime.utcnow().timestamp()}_{user_id}",
            reservation_id=reservation.id
        )
        
        reservation.status = 'confirmed'
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            "message": "Payment processed successfully",
            "payment_id": payment.id,
            "amount": float(payment.amount),
            "reservation_status": reservation.status,
            "car_details": {
                "make": reservation.car.make,
                "model": reservation.car.model
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Payment processing failed",
            "details": str(e)
        }), 500