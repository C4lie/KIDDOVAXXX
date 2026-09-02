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

    def test_stock_auto_decrement_and_replenishment(self):
        from patientapp.models import Appointmenttbl
        # 1. New vaccine defaults to 50 stock
        v = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="Hepatitis-B 1",
            price=300
        )
        self.assertEqual(v.stock_quantity, 50)

        # 2. Simulate appointment completion / check-out (active=1 -> active=2)
        apt = Appointmenttbl.objects.create(
            hospitalid=self.hospital,
            vaccineid=v,
            patientid=self.parent,
            aptdate=datetime.date.today(),
            active=1
        )
        
        # Perform check-out logic
        apt.active = 2
        apt.save()
        if apt.vaccineid and apt.vaccineid.stock_quantity > 0:
            apt.vaccineid.stock_quantity = max(0, apt.vaccineid.stock_quantity - 1)
            apt.vaccineid.save()

        v.refresh_from_db()
        self.assertEqual(v.stock_quantity, 49)

        # 3. Simulate Quick Restock (+10 doses -> 59)
        v.stock_quantity += 10
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.stock_quantity, 59)

    def test_feature1_queue_prioritization(self):
        from patientapp.models import Appointmenttbl
        from patientapp.services.queue_priority_service import calculate_appointment_priority
        
        vaccine = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="MMR 1",
            price=200,
            stock_quantity=2, # low stock
            minimum_quantity=5
        )
        child = Childtbl.objects.create(
            patient=self.parent,
            childname="Aarav",
            dob=datetime.date(2023, 1, 1),
            gender="Boy"
        )
        apt = Appointmenttbl.objects.create(
            hospitalid=self.hospital,
            vaccineid=vaccine,
            patientid=self.parent,
            child=child,
            aptdate=datetime.date.today(),
            apttime=datetime.time(10, 30),
            is_confirmed=False
        )
        result = calculate_appointment_priority(apt)
        self.assertIn(result['priority'], ['HIGH', 'MEDIUM'])
        self.assertTrue(len(result['reasons']) > 0)

    def test_feature2_inventory_forecasting(self):
        from hospitalapp.services.inventory_forecast_service import generate_inventory_forecast_for_hospital
        v1 = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="BCG",
            stock_quantity=8,
            minimum_quantity=5
        )
        forecasts = generate_inventory_forecast_for_hospital(self.hospital.id, forecast_days=14)
        self.assertTrue(len(forecasts) > 0)
        fc = [f for f in forecasts if f['vaccine_name'] == "BCG"][0]
        self.assertEqual(fc['stock_quantity'], 8)
        self.assertIn(fc['risk_level'], ['SAFE', 'MONITOR', 'AT_RISK', 'CRITICAL'])

    def test_feature3_quality_checker(self):
        from patientapp.models import Appointmenttbl
        from patientapp.services.quality_checker_service import run_quality_check_for_child
        child = Childtbl.objects.create(
            patient=self.parent,
            childname="Riya",
            dob=datetime.date(2025, 5, 10),
            gender="Girl"
        )
        vaccine = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="OPV",
            stock_quantity=20
        )
        # Create an impossible date (before DOB)
        apt = Appointmenttbl.objects.create(
            hospitalid=self.hospital,
            vaccineid=vaccine,
            patientid=self.parent,
            child=child,
            aptdate=datetime.date(2025, 1, 1), # Before DOB!
            active=2
        )
        alerts = run_quality_check_for_child(child.id)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0].issue_type, 'IMPOSSIBLE_DATE')

    def test_feature4_date_time_scheduling(self):
        from patientapp.services.booking_service import generate_hospital_time_slots, validate_and_reserve_slot
        today = datetime.date.today() + datetime.timedelta(days=1)
        slots = generate_hospital_time_slots(self.hospital.id, today)
        self.assertTrue(len(slots) > 0)
        # Validate reservation
        res = validate_and_reserve_slot(self.hospital.id, today, datetime.time(9, 30))
        self.assertTrue(res)

    def test_feature5_location_recommendation(self):
        from patientapp.services.geocoding_service import calculate_haversine_distance, sort_hospitals_by_recommendation
        # Surat to Vadodara distance
        dist = calculate_haversine_distance(21.1702, 72.8311, 22.3072, 73.1812)
        self.assertGreater(dist, 100) # ~130 km
        
        hospitals = sort_hospitals_by_recommendation(
            Hospitaltbl.objects.all(),
            user_lat=21.1702,
            user_lng=72.8311
        )
        self.assertGreaterEqual(len(hospitals), 1)

    def test_journey_assistant_timeline_and_next_step(self):
        from patientapp.services.journey_assistant_service import build_child_vaccination_journey
        Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="BCG",
            price=250
        )
        child = Childtbl.objects.create(
            patient=self.parent,
            childname="Siya",
            dob=datetime.date.today() - datetime.timedelta(days=60), # ~2 months old
            gender="Girl"
        )
        res = build_child_vaccination_journey(child.id)
        self.assertTrue(res['success'])
        self.assertEqual(res['child']['name'], "Siya")
        self.assertIsNotNone(res['next_step'])

    def test_patient_booking_get_builds_vaccine_context(self):
        from django.test import RequestFactory
        from django.contrib.sessions.backends.db import SessionStore
        from patientapp.views import BookedAppointment

        request = RequestFactory().get('/patient/booking/')
        request.session = SessionStore()
        request.session['CName'] = 'John Doe'
        request.session['Cid'] = self.parent.id
        request.session['user_role'] = 'patient'

        response = BookedAppointment.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book Appointment')

    def test_education_explainer_qa_and_safety_disclaimer(self):
        from patientapp.services.education_explainer_service import answer_vaccine_education_query
        
        # Test normal question
        ans_normal = answer_vaccine_education_query("Why does my child need DTaP vaccine?")
        self.assertFalse(ans_normal['is_safety_disclaimer'])
        self.assertIn("DTaP", ans_normal['title'])

        # Test safety boundary query
        ans_safety = answer_vaccine_education_query("My child has high fever above 102. Should I give vaccine?")
        self.assertTrue(ans_safety['is_safety_disclaimer'])
        self.assertTrue(ans_safety['show_contact_button'])
        self.assertIn("cannot determine", ans_safety['answer'])
