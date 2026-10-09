"""
patientapp/tests_pincode_service.py
===================================
Unit and Integration tests for Pincode Nearest Hospital Discovery feature.
"""

from django.test import TestCase, Client
from django.urls import reverse
from adminapp.models import City, Area
from hospitalapp.models import Hospitaltbl
from patientapp.models import Patienttbl
from patientapp.services.hospital_pincode_service import find_nearest_hospitals_by_pincode


class PincodeHospitalServiceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(cityName="Vadodara")
        self.area1 = Area.objects.create(cityId=self.city, areaName="Waghodia")
        self.area2 = Area.objects.create(cityId=self.city, areaName="Manjalpur")

        self.h1 = Hospitaltbl.objects.create(
            title="Bapod UPHC",
            dcrname="Dr. Mansuri",
            address="Waghodiya Road, Vadodara",
            pincode="390019",
            cityId=self.city,
            areaId=self.area1,
            contactNo=6357977355,
            password="pass"
        )
        self.h2 = Hospitaltbl.objects.create(
            title="Manjalpur U-CHC",
            dcrname="Dr. Vyas",
            address="Manjalpur, Vadodara",
            pincode="390011",
            cityId=self.city,
            areaId=self.area2,
            contactNo=9227735372,
            password="pass"
        )

    def test_exact_pincode_match(self):
        result = find_nearest_hospitals_by_pincode("390019")
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["exact_count"], 1)
        self.assertTrue(any(h["pincode"] == "390019" for h in result["hospitals"]))
        self.assertTrue(result["hospitals"][0]["is_exact_match"])

    def test_zone_prefix_fallback(self):
        # Query pincode 390025 (no exact match, but matches 3900xx zone)
        result = find_nearest_hospitals_by_pincode("390025")
        self.assertTrue(result["success"])
        self.assertGreater(len(result["hospitals"]), 0)
        self.assertFalse(result["hospitals"][0]["is_exact_match"])

    def test_invalid_pincode_length(self):
        result = find_nearest_hospitals_by_pincode("390")
        self.assertFalse(result["success"])
        self.assertEqual(len(result["hospitals"]), 0)

    def test_pincode_api_endpoint(self):
        url = reverse('patient:api_nearest_hospitals_by_pincode')
        response = self.client.get(url, {'pincode': '390019'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["pincode"], "390019")
        self.assertEqual(data["hospitals"][0]["title"], "Bapod UPHC")

    def test_patient_registration_with_pincode(self):
        register_url = reverse('patient:registerpage')
        post_data = {
            'name': 'Test Guardian',
            'address': '104, Sunrise Apts, Waghodia Road',
            'pincode': '390019',
            'cityId': self.city.id,
            'areaId': self.area1.id,
            'contactNo': '9876543210',
            'password': 'StrongPassword123',
        }
        response = self.client.post(register_url, post_data)
        self.assertEqual(response.status_code, 302)
        patient = Patienttbl.objects.filter(contactNo=9876543210).first()
        self.assertIsNotNone(patient)
        self.assertEqual(patient.pincode, '390019')
