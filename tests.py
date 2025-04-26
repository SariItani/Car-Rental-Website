import unittest
import requests
from datetime import datetime, timedelta
import json
import os

BASE_URL = "http://localhost:5000/api"
ADMIN_EMAIL = "admin@rental.com"
ADMIN_PASSWORD = "admin123"
CLIENT_EMAIL = "client@example.com"
CLIENT_PASSWORD = "client123"

class TestCarRentalAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            # Get admin and client tokens for testing
            cls.admin_token = cls.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
            if not cls.admin_token:
                raise Exception("Admin login failed")
            
            cls.client_token = cls.get_auth_token(CLIENT_EMAIL, CLIENT_PASSWORD)
            if not cls.client_token:
                raise Exception("Client login failed")
            
            # Create a test car as admin
            car_data = {
                "make": "TestMake",
                "model": "TestModel",
                "year": 2023,
                "price_per_day": 50.00,
                "vehicle_type": "sedan",
                "location": "downtown"
            }
            headers = {"Authorization": f"Bearer {cls.admin_token}"}
            response = requests.post(f"{BASE_URL}/admin/cars", json=car_data, headers=headers)
            cls.test_car_id = response.json().get("car_id")
            
            # Create a test reservation as client
            start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            reservation_data = {
                "car_id": cls.test_car_id,
                "start_date": start_date,
                "end_date": end_date
            }
            headers = {"Authorization": f"Bearer {cls.client_token}"}
            response = requests.post(f"{BASE_URL}/cars/reserve", json=reservation_data, headers=headers)
            cls.test_reservation_id = response.json().get("reservation_id")
            
            # Process payment for the reservation
            payment_data = {
                "reservation_id": cls.test_reservation_id,
                "method": "credit_card"
            }
            response = requests.post(f"{BASE_URL}/payments/process", json=payment_data, headers=headers)
            cls.test_payment_id = response.json().get("payment_id")

            damage_data = {
                "description": "Test damage",
                "repair_cost": 100.00
            }
            headers = {"Authorization": f"Bearer {cls.client_token}"}
            response = requests.post(
                f"{BASE_URL}/cars/reservations/{cls.test_reservation_id}/damage",
                json=damage_data,
                headers=headers
            )
            cls.test_damage_id = response.json().get("damage_id")
        
        except Exception as e:
            print(f"Setup failed: {str(e)}")
            cls.tearDownClass()
            raise

    
    @classmethod
    def tearDownClass(cls):
        # Clean up test data
        headers = {"Authorization": f"Bearer {cls.admin_token}"}
        requests.delete(f"{BASE_URL}/admin/cars/{cls.test_car_id}", headers=headers)
    
    @staticmethod
    def get_auth_token(email, password):
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        return response.json().get("access_token")
    
    # Auth Tests
    def test_1_login(self):
        # Test successful login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.assertIn(response.status_code, [200, 201])  # More flexible
        
        # Test invalid credentials
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 401)
    
    def test_2_register(self):
        # Test client registration
        test_email = f"testclient{datetime.now().timestamp()}@example.com"
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": test_email,
                "password": "test123",
                "type": "client",
                "driving_license": "TEST123456",
                "phone": "+1234567890"
            }
        )
        self.assertEqual(response.status_code, 201)
        
        # Test duplicate email
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": test_email,
                "password": "test123",
                "type": "client",
                "driving_license": "TEST123456"
            }
        )
        self.assertEqual(response.status_code, 409)
        
        # Test admin registration (should fail without proper perms)
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"testadmin{datetime.now().timestamp()}@example.com",
                "password": "test123",
                "role": "client",
                "type": "admin"
            }
        )
        self.assertEqual(response.status_code, 400)  # Missing perms
    
    def test_3_get_current_user(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("email"), CLIENT_EMAIL)
        self.assertEqual(response.json().get("role"), "client")
    
    # Cars Tests
    def test_4_get_cars(self):
        response = requests.get(f"{BASE_URL}/cars/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_5_get_car_details(self):
        response = requests.get(f"{BASE_URL}/cars/{self.test_car_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("make"), "TestMake")
    
    def test_6_search_cars(self):
        # First create a car that matches our search criteria
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_car_data = {
            "make": "TestMake",
            "model": "TestModel",
            "year": 2023,
            "price_per_day": 50.00,
            "vehicle_type": "sedan",
            "location": "downtown"
        }
        response = requests.post(
            f"{BASE_URL}/admin/cars",
            json=test_car_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Now search for it
        params = {
            "make": "Test",
            "min_price": 40,
            "max_price": 60,
            "type": "sedan"
        }
        response = requests.get(f"{BASE_URL}/cars/search", params=params)
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertGreater(len(results), 0)
        
        # Verify the car we created is in results
        self.assertTrue(any(car['make'] == 'TestMake' for car in results))
    
    def test_7_reserve_car(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        
        # Create a NEW car specifically for this test
        car_data = {
            "make": "TestReserveCar",
            "model": "ReservationTest",
            "year": 2023,
            "price_per_day": 50.00,
            "vehicle_type": "sedan",
            "location": "downtown"
        }
        response = requests.post(
            f"{BASE_URL}/admin/cars",
            json=car_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(response.status_code, 201)
        car_id = response.json().get("car_id")
        
        # Use dates that definitely won't conflict
        start_date = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=102)).strftime('%Y-%m-%d')
        
        data = {
            "car_id": car_id,
            "start_date": start_date,
            "end_date": end_date,
            "rental_type": "daily"
        }
        
        response = requests.post(
            f"{BASE_URL}/cars/reserve",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Clean up
        requests.delete(
            f"{BASE_URL}/admin/cars/{car_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
    
    def test_8_report_damage(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        data = {
            "description": "Test damage description",
            "repair_cost": 150.50
        }
        response = requests.post(
            f"{BASE_URL}/cars/reservations/{self.test_reservation_id}/damage",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
    
    # Admin Tests
    def test_9_add_car(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data = {
            "make": "AdminTestMake",
            "model": "AdminTestModel",
            "year": 2023,
            "price_per_day": 75.00,
            "vehicle_type": "suv",
            "location": "hotel"
        }
        response = requests.post(f"{BASE_URL}/admin/cars", json=data, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        # Test invalid data
        invalid_data = data.copy()
        invalid_data["year"] = "invalid"
        response = requests.post(f"{BASE_URL}/admin/cars", json=invalid_data, headers=headers)
        self.assertEqual(response.status_code, 400)
    
    def test_10_get_users(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_11_get_all_reservations(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/reservations", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_12_add_insurance(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data = {
            "provider": "TestInsurance",
            "type": "test",
            "expiry_date": (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            "coverage_amount": 50000.00
        }
        response = requests.post(
            f"{BASE_URL}/admin/cars/{self.test_car_id}/insurance",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Test expired date
        invalid_data = data.copy()
        invalid_data["expiry_date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = requests.post(
            f"{BASE_URL}/admin/cars/{self.test_car_id}/insurance",
            json=invalid_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 400)
    
    def test_13_get_damage_reports(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/damage-reports", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_14_update_damage_report(self):
        # First get a damage report ID
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/admin/damage-reports", headers=headers)
        report_id = response.json()[0]["id"]
        
        # Update the report
        data = {
            "status": "inspected",
            "repair_cost": 200.00,
            "description": "Updated description"
        }
        response = requests.put(
            f"{BASE_URL}/admin/damage-reports/{report_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Test invalid status
        invalid_data = data.copy()
        invalid_data["status"] = "invalid_status"
        response = requests.put(
            f"{BASE_URL}/admin/damage-reports/{report_id}",
            json=invalid_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 400)
    
    # Payments Tests
    def test_15_user_reservations(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        response = requests.get(f"{BASE_URL}/payments/reservations", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_16_payment_history(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        response = requests.get(f"{BASE_URL}/payments/history", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
    
    def test_17_process_payment(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        
        # Create a NEW car and reservation
        car_data = {
            "make": "PaymentTestCar",
            "model": "PaymentTest",
            "year": 2023,
            "price_per_day": 50.00,
            "vehicle_type": "sedan",
            "location": "downtown"
        }
        response = requests.post(
            f"{BASE_URL}/admin/cars",
            json=car_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        car_id = response.json().get("car_id")
        
        # Create reservation
        start_date = (datetime.now() + timedelta(days=50)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=52)).strftime('%Y-%m-%d')
        reservation_data = {
            "car_id": car_id,
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.post(
            f"{BASE_URL}/cars/reserve",
            json=reservation_data,
            headers=headers
        )
        reservation_id = response.json().get("reservation_id")
        
        # Process payment
        payment_data = {
            "reservation_id": reservation_id,
            "method": "credit_card"
        }
        response = requests.post(
            f"{BASE_URL}/payments/process",
            json=payment_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Clean up
        requests.delete(
            f"{BASE_URL}/admin/cars/{car_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

    def test_18_terrain_recommendations(self):
        # Create test cars for different terrains
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Desert vehicle (4x4)
        desert_car = {
            "make": "DesertJeep",
            "model": "Wrangler",
            "year": 2023,
            "price_per_day": 100.00,
            "vehicle_type": "4x4",
            "location": "tourist_site"  # Using valid location from VALID_LOCATIONS
        }
        requests.post(f"{BASE_URL}/admin/cars", json=desert_car, headers=headers)
        
        # Mountain vehicle (SUV)
        mountain_car = {
            "make": "MountainSUV",
            "model": "Explorer",
            "year": 2022,
            "price_per_day": 80.00,
            "vehicle_type": "suv",
            "location": "hotel"  # Using valid location from VALID_LOCATIONS
        }
        requests.post(f"{BASE_URL}/admin/cars", json=mountain_car, headers=headers)
        
        # City vehicle (sedan)
        city_car = {
            "make": "CitySedan",
            "model": "Camry",
            "year": 2023,
            "price_per_day": 50.00,
            "vehicle_type": "sedan",
            "location": "downtown"  # Using valid location from VALID_LOCATIONS
        }
        requests.post(f"{BASE_URL}/admin/cars", json=city_car, headers=headers)
        
        # Test desert recommendations
        response = requests.get(f"{BASE_URL}/cars/recommended?terrain=desert")
        self.assertEqual(response.status_code, 200)
        desert_cars = response.json()
        self.assertTrue(all(car['vehicle_type'] == '4x4' for car in desert_cars))
        
        # Test mountain recommendations
        response = requests.get(f"{BASE_URL}/cars/recommended?terrain=mountains")
        self.assertEqual(response.status_code, 200)
        mountain_cars = response.json()
        self.assertTrue(all(car['vehicle_type'] in ['4x4', 'suv'] for car in mountain_cars))
        
        # Test city recommendations (default)
        response = requests.get(f"{BASE_URL}/cars/recommended?terrain=city")
        self.assertEqual(response.status_code, 200)
        city_cars = response.json()
        self.assertTrue(all(car['vehicle_type'] == 'sedan' for car in city_cars))
        
        # Test no terrain specified (should default to city)
        response = requests.get(f"{BASE_URL}/cars/recommended")
        self.assertEqual(response.status_code, 200)
        default_cars = response.json()
        self.assertTrue(all(car['vehicle_type'] == 'sedan' for car in default_cars))

    def test_19_favorites(self):
        headers = {"Authorization": f"Bearer {self.client_token}"}
        
        # Test adding favorite
        response = requests.post(
            f"{BASE_URL}/favorites/cars/{self.test_car_id}/favorite",
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Test getting favorites
        response = requests.get(
            f"{BASE_URL}/favorites/users/me/favorites",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(f['car_id'] == self.test_car_id for f in response.json()))

if __name__ == "__main__":
    unittest.main()