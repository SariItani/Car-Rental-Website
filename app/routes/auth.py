from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.models.user import Admin, Client, User
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Check both User table and specific type table
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Verify password against stored hash
    if not user.check_password(data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Include both role and type in response for consistency
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "role": user.role,
        "type": user.type
    }), 200

@bp.route('/register', methods=['POST'])
def register():
    # f"{BASE_URL}/auth/register",
    # json={
    #     "email": test_email,
    #     "password": "test123",
    #     "role": "client",
    #     "driving_license": "TEST123456"
    # }
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ['email', 'password', 'type']  # Changed from 'role' to 'type'
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
    
    # Check for existing email across all user types
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 409
    
    try:
        if data['type'] == 'admin':
            if not data.get('perms'):
                return jsonify({"error": "Perms are required for admins"}), 400
            
            # Verify admin creation is allowed (e.g., only by other admins)
            new_user = Admin(
                email=data['email'],
                perms=data.get('perms', 'standard'),
                role='admin'  # Explicitly set role
            )
        else:
            if not data.get('driving_license'):
                return jsonify({"error": "Driving license is required for clients"}), 400
                
            new_user = Client(
                email=data['email'],
                phone=data.get('phone'),
                driving_license=data['driving_license'],
                role='client'  # Explicitly set role
            )
        
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "message": "User created successfully",
            "user_id": new_user.id,
            "type": new_user.type,
            "role": new_user.role
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get basic info about the currently authenticated user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    response = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "phone": user.phone
    }
    
    if user.role == 'client':
        response.update({
            "driving_license": user.driving_license
        })

    else:
        response.update({
            "perms": user.perms
        })
    
    return jsonify(response), 200