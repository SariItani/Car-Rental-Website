from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, session
from flask_login import login_user, logout_user, current_user
import requests
from app.forms import LoginForm, RegistrationForm
from app.models.user import User
from flask_jwt_extended import create_access_token, set_access_cookies
from datetime import timedelta

bp = Blueprint('frontend_auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            response = requests.post(
                url_for('auth.login', _external=True),
                json={
                    'email': form.email.data,
                    'password': form.password.data
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                user = User.query.get(data['user_id'])
                if not user:
                    flash('User not found', 'danger')
                    return redirect(url_for('frontend_auth.login'))
                
                if not user.api_token:
                    user.generate_api_token()
                
                login_user(user)
                access_token = create_access_token(
                    identity=user.id,
                    expires_delta=timedelta(hours=1)
                )

                resp = make_response(redirect(url_for('dashboard.dashboard')))
                set_access_cookies(resp, access_token)
                
                session['user_role'] = user.role
                session['user_type'] = user.type
                
                flash('Logged in successfully!', 'success')
                return resp
                
            else:
                flash(response.json().get('error', 'Login failed'), 'danger')
        except requests.exceptions.RequestException as e:
            flash(f'Login error: {str(e)}', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            response = requests.post(
                url_for('auth.register', _external=True),
                json={
                    'email': form.email.data,
                    'password': form.password.data,
                    'type': 'client',
                    'driving_license': form.driving_license.data
                }
            )
            
            if response.status_code == 201:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('frontend_auth.login'))
            else:
                error_msg = response.json().get('error', 'Registration failed')
                flash(f'Registration error: {error_msg}', 'danger')
        except requests.exceptions.RequestException as e:
            flash(f'Registration error: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
def logout():
    from flask_jwt_extended import unset_jwt_cookies
    resp = make_response(redirect(url_for('main.index')))
    logout_user()
    unset_jwt_cookies(resp)
    flash('You have been logged out.', 'info')
    return resp