# routes/frontend/dashboard.py
import os
from flask import Blueprint, current_app, g, render_template
from flask_login import login_required
import requests

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def dashboard():
    reservations = requests.get(
        f"{current_app.config['API_BASE_URL']}/payments/reservations",
        headers={'Authorization': f'Bearer {g.user.api_token}'}
    ).json()
    return render_template('users/dashboard.html', reservations=reservations)