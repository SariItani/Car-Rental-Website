from app.models.user import User, Admin
from flask import jsonify
from datetime import datetime

def error_response(message, status_code, details=None):
    return jsonify({
        "error": {
            "message": message,
            "code": status_code,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    }), status_code

def validate_date(date_str, format='%Y-%m-%d'):
    try:
        return datetime.strptime(date_str, format).date()
    except ValueError:
        return None

def validate_admin_access(user_id):
    user = User.query.get(user_id)
    if not user or user.role != 'admin' or user.type != 'admin':
        return False
    return True