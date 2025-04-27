from pathlib import Path
from app import create_app
from app.models import User, Car, Insurance, db
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app.models.user import Admin, Client

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(email='admin@rental.com').first():
            admin = Admin(
                email='admin@rental.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                type='admin',
                perms='full'
            )
            db.session.add(admin)
            
            client = Client(
                email='client@example.com',
                password_hash=generate_password_hash('client123'),
                role='client',
                type='client',
                driving_license="TEST1234"
            )
            db.session.add(client)


            # Add sample cars with insurance
            cars = [
                Car(
                    make='Toyota', 
                    model='Camry', 
                    year=2022, 
                    price_per_day=50,
                    vehicle_type='sedan',
                    location='city'
                ),
                Car(
                    make='Ford', 
                    model='Explorer', 
                    year=2021, 
                    price_per_day=75,
                    vehicle_type='suv',
                    location='mountains'
                ),
                Car(
                    make='Jeep', 
                    model='Wrangler', 
                    year=2023, 
                    price_per_day=100,
                    vehicle_type='4x4',
                    location='desert'
                )
            ]
            db.session.add_all(cars)
            db.session.flush()
            
            # Add insurance for each car
            insurances = [
                Insurance(
                    provider='Allianz',
                    type='comprehensive',
                    expiry_date=date.today() + timedelta(days=365),
                    coverage_amount=50000,
                    car_id=cars[0].id
                ),
                Insurance(
                    provider='AXA',
                    type='comprehensive',
                    expiry_date=date.today() + timedelta(days=180),
                    coverage_amount=75000,
                    car_id=cars[1].id
                ),
                Insurance(
                    provider='Generali',
                    type='offroad',
                    expiry_date=date.today() + timedelta(days=270),
                    coverage_amount=100000,
                    car_id=cars[2].id
                )
            ]
            db.session.add_all(insurances)
            
            db.session.commit()
            print("Database initialized.")
        else:
            print("Database already initialized")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
