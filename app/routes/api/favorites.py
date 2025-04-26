from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Favorite, db

bp = Blueprint('favorites', __name__)

@bp.route('/cars/<int:car_id>/favorite', methods=['POST'])
@jwt_required()
def add_favorite(car_id):
    user_id = get_jwt_identity()
    
    # Check if already favorited
    if Favorite.query.filter_by(user_id=user_id, car_id=car_id).first():
        return jsonify({"error": "Car already favorited"}), 400
    
    favorite = Favorite(user_id=user_id, car_id=car_id)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({
        "message": "Car added to favorites",
        "favorite_id": favorite.id
    }), 201

@bp.route('/users/me/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = get_jwt_identity()
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    return jsonify([{
        "car_id": f.car_id,
        "created_at": f.created_at.isoformat()
    } for f in favorites])