from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from datetime import datetime
from app.models import Car, DamageReport, Reservation, db

bp = Blueprint('cars', __name__)

@bp.route('/', methods=['GET'])
def get_cars():
    """Get all available cars with basic info"""
    try:
        cars = Car.query.filter_by(status='available').all()
        return jsonify([{
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'price_per_day': float(car.price_per_day),
            'vehicle_type': car.vehicle_type,
            'location': car.location
        } for car in cars])
    except Exception as e:
        return jsonify({"error": "Failed to retrieve cars", "details": str(e)}), 500

@bp.route('/<int:car_id>', methods=['GET'])
def get_car_details(car_id):
    """Get detailed information about a specific car"""
    try:
        car = Car.query.get_or_404(car_id)
        return jsonify({
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'price_per_day': float(car.price_per_day),
            'status': car.status,
            'vehicle_type': car.vehicle_type,
            'location': car.location,
            'insurance': [{
                'provider': ins.provider,
                'type': ins.type,
                'expiry_date': ins.expiry_date.isoformat()
            } for ins in car.insurances] if car.insurances else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/reserve', methods=['POST'])
@jwt_required()
def reserve_car():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    required_fields = ['car_id', 'start_date', 'end_date']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "missing": [f for f in required_fields if f not in data],
            "required": required_fields
        }), 400
    
    try:
        user_id = get_jwt_identity()
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Validate date range
        if start_date >= end_date:
            return jsonify({
                "error": "Invalid date range",
                "message": "End date must be after start date",
                "start_date": data['start_date'],
                "end_date": data['end_date']
            }), 400
            
        if start_date < datetime.now().date():
            return jsonify({
                "error": "Invalid start date",
                "message": "Start date cannot be in the past",
                "start_date": data['start_date'],
                "current_date": datetime.now().date().isoformat()
            }), 400

        car = Car.query.get(data['car_id'])
        if not car:
            return jsonify({
                "error": "Car not found",
                "car_id": data['car_id']
            }), 404
        
        if not car.is_available(start_date, end_date):
            # Get conflicting reservations for better error reporting
            conflicts = Reservation.query.filter(
                Reservation.car_id == car.id,
                Reservation.end_date >= start_date,
                Reservation.start_date <= end_date,
                Reservation.status != 'cancelled'
            ).all()
            
            return jsonify({
                "error": "Car not available",
                "message": "The car is already booked for the selected dates",
                "conflicting_reservations": [
                    {
                        "id": r.id,
                        "start_date": r.start_date.isoformat(),
                        "end_date": r.end_date.isoformat(),
                        "status": r.status
                    } for r in conflicts
                ]
            }), 400

        # Calculate price
        rental_type = data.get('rental_type', 'daily')
        days = (end_date - start_date).days
        
        if rental_type == 'monthly':
            total_price = float(car.price_per_day) * 30 * 0.9  # 10% monthly discount
        elif rental_type == 'yearly':
            total_price = float(car.price_per_day) * 365 * 0.8  # 20% yearly discount
        else:
            total_price = float(car.price_per_day) * days

        # Create reservation
        reservation = Reservation(
            user_id=user_id,
            car_id=car.id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            rental_type=rental_type,
            status='pending'
        )

        db.session.add(reservation)
        db.session.commit()

        return jsonify({
            "message": "Reservation created",
            "reservation_id": reservation.id,
            "total_price": total_price,
            "currency": "USD"
        }), 201
        
    except ValueError as e:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/search', methods=['GET'])
def search_cars():
    """Search for available cars with filters"""
    try:
        # Get and validate filters
        make = request.args.get('make')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        vehicle_type = request.args.get('type')
        location = request.args.get('location')
        
        query = Car.query.filter_by(status='available')
        
        if vehicle_type and vehicle_type in Car.VALID_TYPES:
            query = query.filter_by(vehicle_type=vehicle_type)
        if location and location in Car.VALID_LOCATIONS:
            query = query.filter_by(location=location)
        if make:
            query = query.filter(Car.make.ilike(f'%{make}%'))
        if min_price is not None and min_price >= 0:
            query = query.filter(Car.price_per_day >= min_price)
        if max_price is not None and max_price > 0:
            query = query.filter(Car.price_per_day <= max_price)

        cars = query.all()
        return jsonify([{
            'id': car.id,
            'make': car.make,
            'model': car.model,
            'price_per_day': float(car.price_per_day),
            'vehicle_type': car.vehicle_type,
            'location': car.location
        } for car in cars])
        
    except Exception as e:
        return jsonify({"error": "Search failed", "details": str(e)}), 500

@bp.route('/reservations/<int:reservation_id>/damage', methods=['POST'])
@jwt_required()
def report_damage(reservation_id):
    """Report damage for a specific reservation"""
    required_fields = ['description', 'repair_cost']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        user_id = get_jwt_identity()
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=user_id
        ).first_or_404()

        # if reservation.end_date > datetime.now().date():
        #     return jsonify({"error": "Cannot report damage before rental ends"}), 400

        damage_report = DamageReport(
            description=data['description'],
            repair_cost=data['repair_cost'],
            status='reported',
            reservation_id=reservation_id
        )
        
        reservation.damage_charge = data['repair_cost']
        reservation.car.status = 'maintenance'
        
        db.session.add(damage_report)
        db.session.commit()
        
        return jsonify({
            "message": "Damage reported successfully",
            "damage_id": damage_report.id,
            "car_status": "maintenance"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500