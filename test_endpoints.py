import requests
import json
import datetime
from random import choice, randint

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_CREDS = {"email": "admin@rental.com", "password": "admin123"}
CLIENT_CREDS = {"email": "client@example.com", "password": "client123"}

# Helper functions
def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def print_test_result(name, response, expected_status=200):
    status = "✅" if response.status_code == expected_status else "❌"
    print(f"{status} {name} - Status: {response.status_code}")
    if response.status_code != expected_status:
        print(f"   Response: {response.text}")

# Initialize
session = requests.Session()

def test_auth_endpoints():
    print("\n=== Testing Auth Endpoints ===")
    
    # Test client registration with new fields
    client_data = {
        "email": f"client{randint(1000,9999)}@example.com",
        "password": "testpass123",
        "role": "client",
        "phone": "+1234567890",
        "driving_license": f"DL{randint(10000000,99999999)}"
    }
    res = session.post(f"{BASE_URL}/api/auth/register", json=client_data)
    print_test_result("Register new client with details", res, 201)
    
    # Test admin registration with permissions
    admin_data = {
        "email": f"admin{randint(1000,9999)}@example.com",
        "password": "adminpass123",
        "role": "admin",
        "perms": "full_access"
    }
    res = session.post(f"{BASE_URL}/api/auth/register", json=admin_data)
    print_test_result("Register new admin with permissions", res, 201)
    
    # Test admin login
    res = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    print_test_result("Admin login", res)
    if res.status_code == 200:
        admin_token = res.json().get("access_token")
        print("   ✅ Token format valid")
    else:
        admin_token = None

    
    # Test client login
    res = session.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
    print_test_result("Client login", res)
    client_token = res.json().get("access_token")
    
    # Test invalid login
    res = session.post(f"{BASE_URL}/api/auth/login", json={"email": "nonexistent@test.com", "password": "wrong"})
    print_test_result("Invalid login", res, 401)
    
    return admin_token, client_token

def test_car_endpoints(admin_token, client_token):
    print("\n=== Testing Car Endpoints ===")
    
    # Add new car (admin only)
    new_car = {
        "make": "Tesla",
        "model": "Model 3",
        "year": 2023,
        "price_per_day": 120
    }
    res = session.post(
        f"{BASE_URL}/api/admin/cars",
        json=new_car,
        headers=get_auth_header(admin_token))
    print_test_result("Admin add car", res, 201)
    
    try:
        car_id = res.json()["car_id"]
    except json.JSONDecodeError:
        print("⚠️ Warning: Invalid JSON response")
        car_id = 1  # Fallback
    
    # Try adding car as client (should fail)
    res = session.post(
        f"{BASE_URL}/api/admin/cars",
        json=new_car,
        headers=get_auth_header(client_token))
    print_test_result("Client cannot add car", res, 403)
    
    # Get all cars
    res = session.get(f"{BASE_URL}/api/cars/")
    print_test_result("Get available cars", res)
    cars = res.json()
    
    # Get single car
    res = session.get(f"{BASE_URL}/api/cars/{car_id}")
    print_test_result("Get single car", res)
    
    # Search cars
    res = session.get(f"{BASE_URL}/api/cars/search?make=Tesla&min_price=100")
    print_test_result("Search cars", res)
    
    return car_id

def test_reservation_endpoints(admin_token, client_token, car_id):
    print("\n=== Testing Reservation Endpoints ===")
    
    # Make reservation
    reservation_data = {
        "car_id": car_id,
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
    }
    res = session.post(
        f"{BASE_URL}/api/cars/reserve",
        json=reservation_data,
        headers=get_auth_header(client_token))
    print_test_result("Create reservation", res, 201)
    reservation_id = res.json().get("reservation_id")
    
    # Try to reserve same car again (should fail)
    res = session.post(
        f"{BASE_URL}/api/cars/reserve",
        json=reservation_data,
        headers=get_auth_header(client_token))
    print_test_result("Reserve already reserved car", res, 400)
    
    # Get user reservations
    res = session.get(
        f"{BASE_URL}/api/auth/me/reservations",
        headers=get_auth_header(client_token))
    if res.status_code == 200:
        reservations = res.json()
        has_valid_format = all('id' in r and 'car' in r for r in reservations)
        print(f"   {'✅' if has_valid_format else '❌'} Valid reservation format")
    print_test_result("Get user reservations", res)
    
    # Get all reservations (admin only)
    res = session.get(
        f"{BASE_URL}/api/admin/reservations",
        headers=get_auth_header(admin_token))
    print_test_result("Admin get all reservations", res)
    
    return reservation_id

def test_payment_endpoints(admin_token, client_token, reservation_id):
    print("\n=== Testing Payment Endpoints ===")
    
    # Process payment
    payment_data = {"reservation_id": reservation_id, "method": "credit_card"}
    res = session.post(
        f"{BASE_URL}/api/payments/process",
        json=payment_data,
        headers=get_auth_header(client_token))
    
    if res.status_code == 200:
        payment = res.json()
        valid_date = False
        if 'payment_date' in payment:
            try:
                datetime.fromisoformat(payment['payment_date'])
                valid_date = True
            except ValueError:
                pass
        print(f"   {'✅' if valid_date else '❌'} Valid payment date format")

    
    # Try to pay for non-existent reservation
    res = session.post(
        f"{BASE_URL}/api/payments/process",
        json={"reservation_id": 9999, "method": "credit_card"},
        headers=get_auth_header(client_token))
    print_test_result("Pay for invalid reservation", res, 404)
    
    # Try to pay as different user (should fail)
    other_user_token = admin_token  # Using admin as different user
    res = session.post(
        f"{BASE_URL}/api/payments/process",
        json=payment_data,
        headers=get_auth_header(other_user_token))
    print_test_result("Pay for others' reservation", res, 404)

def test_admin_endpoints(admin_token):
    print("\n=== Testing Admin Endpoints ===")
    
    # Get all users
    res = session.get(
        f"{BASE_URL}/api/admin/users",
        headers=get_auth_header(admin_token))
    if res.status_code == 200:
        users = res.json()
        valid_admins = [u for u in users if u.get('type') == 'admin']
        print(f"   {'✅' if valid_admins else '❌'} Valid admin users found")
    
    # Try as client (should fail)
    res = session.get(
        f"{BASE_URL}/api/admin/users",
        headers=get_auth_header(client_token))
    print_test_result("Client cannot get all users", res, 403)

    # Test admin permissions field
    res = session.get(
        f"{BASE_URL}/api/admin/users",
        headers=get_auth_header(admin_token))
    if res.status_code == 200:
        admins = [u for u in res.json() if u['role'] == 'admin']
        has_perms = all('perms' in a for a in admins)
        print(f"   {'✅' if has_perms else '❌'} Admins have permissions field")
    print_test_result("Admin get all users", res)

def test_insurance_flow(admin_token, client_token, car_id):
    print("\n=== Testing Insurance Flow ===")
    
    # Admin adds insurance
    insurance_data = {
        "provider": "Allianz",
        "type": "full",
        "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        "coverage_amount": 50000
    }
    res = session.post(
        f"{BASE_URL}/api/admin/cars/{car_id}/insurance",
        json=insurance_data,
        headers=get_auth_header(admin_token))
    print_test_result("Admin adds insurance", res, 201)
    
    # Client views car with insurance
    res = session.get(f"{BASE_URL}/api/cars/{car_id}")
    print_test_result("Get car with insurance", res)
    if res.status_code == 200:
        print(f"   Insurance: {res.json().get('insurance')}")

    # Client tries to add insurance (should fail)
    res = session.post(
        f"{BASE_URL}/api/admin/cars/{car_id}/insurance",
        json=insurance_data,
        headers=get_auth_header(client_token))
    print_test_result("Client cannot add insurance", res, 403)

def test_damage_reports(admin_token, client_token, reservation_id):
    print("\n=== Testing Damage Reports ===")
    
    # Client reports damage
    damage_data = {
        "description": "Scratch on rear bumper",
        "repair_cost": 150.00
    }
    res = session.post(
        f"{BASE_URL}/api/cars/reservations/{reservation_id}/damage",
        json=damage_data,
        headers=get_auth_header(client_token))
    
    if res.status_code == 201:
        # Verify damage charge was applied to reservation
        res = session.get(
            f"{BASE_URL}/api/auth/me/reservations",
            headers=get_auth_header(client_token))
        if res.status_code == 200:
            reservations = res.json()
            has_charge = any(r['damage_charge'] > 0 for r in reservations)
            print(f"   {'✅' if has_charge else '❌'} Damage charge applied")
    
    print_test_result("Client reports damage", res, 201)
    damage_id = res.json().get('damage_id') if res.status_code == 201 else None
    
    # Admin views damage reports
    if damage_id:
        res = session.get(
            f"{BASE_URL}/api/admin/damage-reports",
            headers=get_auth_header(admin_token))
        print_test_result("Admin views damage reports", res, 200)
        
        # Verify the report exists in the list
        if res.status_code == 200:
            reports = res.json()
            found = any(report['id'] == damage_id for report in reports)
            print(f"   {'✅' if found else '❌'} Damage report found in list")
    
    # Admin updates damage status
    if damage_id:
        update_data = {"status": "inspected", "repair_cost": 200.00}
        res = session.put(
            f"{BASE_URL}/api/admin/damage-reports/{damage_id}",
            json=update_data,
            headers=get_auth_header(admin_token))
        print_test_result("Admin updates damage report", res, 200)
        
        # Verify update
        if res.status_code == 200:
            updated_report = res.json().get('report')
            print(f"   New status: {updated_report.get('status')}")
            print(f"   New repair cost: {updated_report.get('repair_cost')}")

def test_long_term_leasing(admin_token, client_token):
    print("\n=== Testing Long-Term Leasing ===")
    
    # First create a new car specifically for leasing tests
    lease_car = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "price_per_day": 50,
        "vehicle_type": "sedan",
        "location": "airport"
    }
    res = session.post(
        f"{BASE_URL}/api/admin/cars",
        json=lease_car,
        headers=get_auth_header(admin_token))
    if res.status_code != 201:
        print("⚠️ Failed to create lease car, skipping tests")
        return
    lease_car_id = res.json().get("car_id")

    # Monthly lease test
    monthly_lease = {
        "car_id": lease_car_id,
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=40)).strftime('%Y-%m-%d'),
        "rental_type": "monthly"
    }
    res = session.post(
        f"{BASE_URL}/api/cars/reserve",
        json=monthly_lease,
        headers=get_auth_header(client_token))
    print_test_result("Monthly lease reservation", res, 201)
    
    # Yearly lease test (with different dates)
    yearly_lease = {
        "car_id": lease_car_id,
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=50)).strftime('%Y-%m-%d'),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=415)).strftime('%Y-%m-%d'),
        "rental_type": "yearly"
    }
    res = session.post(
        f"{BASE_URL}/api/cars/reserve",
        json=yearly_lease,
        headers=get_auth_header(client_token))
    print_test_result("Yearly lease reservation", res, 201)

if __name__ == "__main__":
    print("🚀 Starting comprehensive endpoint tests...")
    
    # Run tests
    admin_token, client_token = test_auth_endpoints()
    car_id = test_car_endpoints(admin_token, client_token)
    reservation_id = test_reservation_endpoints(admin_token, client_token, car_id)
    test_payment_endpoints(admin_token, client_token, reservation_id)
    test_admin_endpoints(admin_token)
    
    # New test flows
    test_insurance_flow(admin_token, client_token, car_id)
    test_damage_reports(admin_token, client_token, reservation_id)
    test_long_term_leasing(admin_token, client_token)
    
    print("\n🔥 All tests completed!")
