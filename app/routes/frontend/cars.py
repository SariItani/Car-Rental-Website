from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import login_required
import requests
from app.forms import ReservationForm
import os
from app.models import Car
from app import db

bp = Blueprint('frontend_cars', __name__, url_prefix='/cars')

@bp.route('/')
def list():
    make = request.args.get('make')
    vehicle_type = request.args.get('type')
    
    query = Car.query.filter_by(status='available')
    if make:
        query = query.filter(Car.make.ilike(f'%{make}%'))
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)
    
    return render_template('cars/list.html', cars=query.all())

@bp.route('/<int:car_id>')
def detail(car_id):
    car = Car.query.get_or_404(car_id)
    form = ReservationForm()
    return render_template('cars/detail.html', car=car, form=form)

@bp.route('/<int:car_id>/reserve', methods=['POST'])
@login_required
def reserve(car_id):
    form = ReservationForm()
    if form.validate_on_submit():
        reservation_data = {
            'car_id': car_id,
            'start_date': form.start_date.data.isoformat(),
            'end_date': form.end_date.data.isoformat()
        }
        response = requests.post(
            f"{current_app.config['API_BASE_URL']}/reservations",
            json=reservation_data,
            headers={'Authorization': f'Bearer {g.user.api_token}'}
        )
        if response.status_code == 201:
            flash('Reservation successful!', 'success')
            return redirect(url_for('frontend_cars.detail', car_id=car_id))
        flash(response.json().get('error', 'Reservation failed'), 'danger')
    return render_template('cars/detail.html', car=Car.query.get(car_id), form=form)