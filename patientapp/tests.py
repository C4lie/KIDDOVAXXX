from django.test import TestCase
from patientapp.models import Patienttbl, Childtbl, VaccineCardUpload
from hospitalapp.models import Hospitaltbl, Vaccinetbl, VaccineInfo
from adminapp.models import City, Area
import datetime

class KiddoVaxV2Tests(TestCase):
    def setUp(self):
        # Create master data
        self.city = City.objects.create(cityName="Surat")
        self.area = Area.objects.create(cityId=self.city, areaName="Adajan")
        
        # Create parent patient
        self.parent = Patienttbl.objects.create(
            name="John Doe",
            address="123 Street",
            cityId=self.city,
            areaId=self.area,
            contactNo=1234567890,
            password="password123"
        )
        
        # Create hospital
        self.hospital = Hospitaltbl.objects.create(
            title="Surat Pediatric Clinic",
            address="456 Avenue",
            cityId=self.city,
            areaId=self.area,
            contactNo=987654321,
            password="hosp_password"
        )

    def test_child_profile_blood_group(self):
        # Create child with blood group
        child = Childtbl.objects.create(
            patient=self.parent,
            childname="Baby Doe",
            dob=datetime.date(2024, 1, 15),
            gender="Boy",
            blood_group="AB+"
        )
        self.assertEqual(child.blood_group, "AB+")
        self.assertEqual(child.age, datetime.date.today().year - 2024 - ((datetime.date.today().month, datetime.date.today().day) < (1, 15)))

    def test_vaccine_stock_fields(self):
        # Create vaccine with stock
        vaccine = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="BCG",
            vaccineDescr="Tuberculosis vaccine",
            price=150,
            stock_quantity=10,
            minimum_quantity=3
        )
        self.assertEqual(vaccine.stock_quantity, 10)
        self.assertEqual(vaccine.minimum_quantity, 3)

    def test_ocr_fallback(self):
        from patientapp.ocr_service import extract_vaccine_data_from_image
        # Testing ocr service fallback logic
        dob = datetime.date(2025, 1, 1)
        res = extract_vaccine_data_from_image("mock_path.png", dob)
        
        self.assertEqual(res["method"], "Mock Fallback Engine")
        self.assertEqual(len(res["vaccines"]), 3)
        self.assertEqual(res["vaccines"][0]["name"], "BCG")
        self.assertEqual(res["vaccines"][0]["date"], "2025-01-02")

    def test_pdf_generation_qr_content(self):
        from patientapp.pdf_service import generate_vaccine_card_pdf
        # Create a child
        child = Childtbl.objects.create(
            patient=self.parent,
            childname="Baby Doe",
            dob=datetime.date(2024, 1, 15),
            gender="Boy",
            blood_group="AB+"
        )
        pdf_bytes = generate_vaccine_card_pdf(child)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 0)

    def test_translation_middleware_hindi(self):
        from django.test import RequestFactory
        from django.http import HttpResponse
        from patientapp.middleware import AutoTranslationMiddleware
        
        # Setup request
        request = RequestFactory().get('/patient/')
        request.session = {'django_language': 'hi'}
        
        # Setup dummy response
        def get_response(req):
            return HttpResponse(
                "<html><body><h1>Prevent the Spread</h1><p>Stay at Home, Stay Safe.</p></body></html>",
                content_type="text/html"
            )
            
        middleware = AutoTranslationMiddleware(get_response)
        response = middleware(request)
        
        # Assert content was translated
        self.assertIn("प्रसार रोकें", response.content.decode('utf-8'))
        self.assertIn("घर पर रहें, सुरक्षित रहें।", response.content.decode('utf-8'))
        self.assertNotIn("Prevent the Spread", response.content.decode('utf-8'))
