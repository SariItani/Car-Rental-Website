from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Refund, Reservation, db

bp = Blueprint('refunds', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def request_refund():
    data = request.get_json()
    if not data or 'reservation_id' not in data:
        return jsonify({"error": "Missing reservation_id"}), 400

    # Debug: Print received data
    print(f"Refund request data: {data}")

    reservation = Reservation.query.filter_by(
        id=data['reservation_id'],
        user_id=get_jwt_identity()
    ).first()

    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404

    # Allow refunds only for completed/cancelled reservations
    if reservation.status not in ['completed', 'cancelled']:
        return jsonify({
            "error": "Refund only allowed for completed/cancelled reservations",
            "current_status": reservation.status
        }), 400

    refund = Refund(
        reservation_id=reservation.id,
        amount=reservation.total_price * 0.8,
        reason=data.get('reason', '')
    )
    db.session.add(refund)
    db.session.commit()
    
    return jsonify(refund.to_dict()), 201

@bp.route('/<int:refund_id>', methods=['PUT'])
@jwt_required()
def process_refund(refund_id):
    refund = Refund.query.get_or_404(refund_id)
    if refund.reservation.user_id != get_jwt_identity():
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if data.get('status') in ['approved', 'rejected']:
        refund.status = data['status']
        refund.processed_at = datetime.utcnow()
        db.session.commit()
    return jsonify(refund.to_dict())