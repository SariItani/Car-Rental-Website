from datetime import datetime
from flask import Blueprint, jsonify, request
from flask import make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from app.models import DamageReport, Insurance, Reservation, User, Car, db
from app.models.payment import Payment
from app.models.user import Admin, Client
from app.utils import validate_admin_access

bp = Blueprint('admin', __name__)

def validate_car_data(data):
    """Validate car creation/update data"""
    required_fields = ['make', 'model', 'year', 'price_per_day']
    if not all(field in data for field in required_fields):
        return False, "Missing required fields"
    
    if not isinstance(data['year'], int) or data['year'] < 1900 or data['year'] > datetime.now().year + 1:
        return False, "Invalid year"
    
    if float(data['price_per_day']) <= 0:
        return False, "Price must be positive"
    
    if data.get('vehicle_type') and data['vehicle_type'] not in Car.VALID_TYPES:
        return False, f"Invalid vehicle type. Must be one of {Car.VALID_TYPES}"
    
    if data.get('location') and data['location'] not in Car.VALID_LOCATIONS:
        return False, f"Invalid location. Must be one of {Car.VALID_LOCATIONS}"
    
    return True, None

@bp.route('/cars', methods=['POST'])
@jwt_required()
def add_car():
    """Add a new car to the fleet"""
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    is_valid, error = validate_car_data(data)
    if not is_valid:
        return jsonify({"error": error}), 400

    try:
        new_car = Car(
            make=data['make'],
            model=data['model'],
            year=data['year'],
            price_per_day=data['price_per_day'],
            vehicle_type=data.get('vehicle_type', 'sedan'),
            location=data.get('location', 'downtown')
        )
        
        db.session.add(new_car)
        db.session.commit()
        
        return jsonify({
            "message": "Car added successfully",
            "car_id": new_car.id,
            "details": {
                "make": new_car.make,
                "model": new_car.model,
                "status": new_car.status
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/reservations', methods=['GET'])
@jwt_required()
def get_all_reservations():
    """Get all reservations with detailed information"""
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        reservations = Reservation.query.options(
            joinedload(Reservation.user),
            joinedload(Reservation.car),
            joinedload(Reservation.payment),
            joinedload(Reservation.damage_reports)
        ).order_by(
            Reservation.start_date.desc()
        ).all()
        
        return jsonify([{
            'id': r.id,
            'user': {
                'id': r.user.id,
                'email': r.user.email
            },
            'car': {
                'id': r.car.id,
                'make': r.car.make,
                'model': r.car.model
            },
            'dates': {
                'start': r.start_date.isoformat(),
                'end': r.end_date.isoformat()
            },
            'status': r.status,
            'total_price': float(r.total_price),
            'payment_status': r.payment.status if r.payment else None,
            'has_damage': len(r.damage_reports) > 0
        } for r in reservations])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/cars/<int:car_id>/insurance', methods=['POST'])
@jwt_required()
def add_insurance(car_id):
    """Add insurance to a specific car"""
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    car = Car.query.get(car_id)
    if not car:
        return jsonify({"error": "Car not found"}), 404
        
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ['provider', 'type', 'expiry_date', 'coverage_amount']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
    
    try:
        expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        if expiry_date < datetime.now().date():
            return jsonify({"error": "Expiry date cannot be in the past"}), 400
            
        if float(data['coverage_amount']) <= 0:
            return jsonify({"error": "Coverage amount must be positive"}), 400

        new_insurance = Insurance(
            provider=data['provider'],
            type=data['type'],
            expiry_date=expiry_date,
            coverage_amount=data['coverage_amount'],
            car_id=car_id
        )
        
        db.session.add(new_insurance)
        db.session.commit()
        
        return jsonify({
            "message": "Insurance added successfully",
            "insurance_id": new_insurance.id,
            "details": {
                "provider": new_insurance.provider,
                "expiry_date": new_insurance.expiry_date.isoformat(),
                "car_id": car_id
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/damage-reports', methods=['GET'])
@jwt_required()
def get_damage_reports():
    """Get all damage reports with detailed information"""
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        reports = DamageReport.query.options(
            joinedload(DamageReport.reservation).joinedload(Reservation.car),
            joinedload(DamageReport.reservation).joinedload(Reservation.user)
        ).order_by(
            DamageReport.created_at.desc()
        ).all()
        
        return jsonify([{
            'id': report.id,
            'reservation': {
                'id': report.reservation.id,
                'user': report.reservation.user.email,
                'car': f"{report.reservation.car.make} {report.reservation.car.model}"
            },
            'description': report.description,
            'repair_cost': float(report.repair_cost),
            'status': report.status,
            'reported_at': report.created_at.isoformat(),
            'last_updated': report.updated_at.isoformat() if hasattr(report, 'updated_at') else None
        } for report in reports])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/damage-reports/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_damage_report(report_id):
    """Update a damage report"""
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    report = DamageReport.query.get_or_404(report_id)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    
    valid_statuses = ['reported', 'inspected', 'repaired', 'disputed']
    if 'status' in data and data['status'] not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400
    
    if 'repair_cost' in data and float(data['repair_cost']) <= 0:
        return jsonify({"error": "Repair cost must be positive"}), 400
    
    try:
        if 'status' in data:
            report.status = data['status']
        if 'repair_cost' in data:
            report.repair_cost = data['repair_cost']
        if 'description' in data:
            report.description = data['description']
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Damage report updated successfully",
            "report": {
                "id": report.id,
                "status": report.status,
                "repair_cost": float(report.repair_cost),
                "updated_at": report.updated_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    # Get top 3 popular cars
    popular = db.session.query(
        Reservation.car_id,
        Car.make,
        Car.model,
        db.func.count(Reservation.id).label('count')
    ).join(Car).group_by(Reservation.car_id, Car.make, Car.model)\
    .order_by(db.func.count(Reservation.id).desc())\
    .limit(3).all()

    return jsonify({
        'reservations_count': Reservation.query.count(),
        'revenue': float(db.session.query(db.func.sum(Payment.amount)).scalar() or 0),
        'damage_costs': float(db.session.query(db.func.sum(DamageReport.repair_cost)).scalar() or 0),
        'popular_cars': [
            {
                'car_id': car_id,
                'make': make,
                'model': model,
                'reservation_count': count
            } for car_id, make, model, count in popular
        ]
    })

@bp.route('/reservations/export', methods=['GET'])
@jwt_required()
def export_reservations():
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    reservations = Reservation.query.options(
        joinedload(Reservation.user),
        joinedload(Reservation.car)
    ).all()
    
    csv_data = "ID,User Email,Car Make,Car Model,Start Date,End Date,Total Price,Status\n"
    for r in reservations:
        csv_data += (
            f"{r.id},{r.user.email},{r.car.make},{r.car.model},"
            f"{r.start_date},{r.end_date},{r.total_price},{r.status}\n"
        )
    
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=reservations.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@bp.route('/reservations/<int:reservation_id>', methods=['PUT'])
@jwt_required()
def update_reservation(reservation_id):
    if not validate_admin_access(get_jwt_identity()):
        return jsonify({"error": "Admin access required"}), 403
    
    reservation = Reservation.query.get_or_404(reservation_id)
    data = request.get_json()
    
    if 'status' in data and data['status'] in Reservation.VALID_STATUSES:
        reservation.status = data['status']
        db.session.commit()
        return jsonify({"message": "Reservation updated"}), 200
    
    return jsonify({"error": "Invalid update"}), 400