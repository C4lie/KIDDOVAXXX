import datetime
from django.test import TestCase, Client
from django.urls import reverse
from patientapp.models import Patienttbl, Childtbl, Appointmenttbl
from hospitalapp.models import Hospitaltbl, Vaccinetbl, HospitalHoliday
from adminapp.models import City, Area
from patientapp.services.ai_assistant_service import (
    process_ai_message,
    detect_intent,
    extract_matched_vaccine_key,
    extract_child_age_days,
    extract_date_from_text,
    extract_time_slot_from_text
)


class AIAssistantTests(TestCase):
    def setUp(self):
        self.city = City.objects.create(cityName="Surat")
        self.area = Area.objects.create(cityId=self.city, areaName="Athwa")

        self.patient = Patienttbl.objects.create(
            name="Rahul Sharma",
            address="101 Riverfront Apartments",
            cityId=self.city,
            areaId=self.area,
            contactNo=9876543210,
            password="securepassword",
            account_status='ACTIVE',
            must_change_password=False
        )

        self.child = Childtbl.objects.create(
            patient=self.patient,
            childname="Aarav",
            dob=datetime.date.today() - datetime.timedelta(days=270), # ~9 months old
            gender="Boy"
        )

        self.hospital = Hospitaltbl.objects.create(
            title="City Care Pediatric Hospital",
            address="Ring Road, Surat",
            cityId=self.city,
            areaId=self.area,
            contactNo=9123456780,
            password="hospitalpass",
            opening_time=datetime.time(9, 0),
            closing_time=datetime.time(17, 0),
            slot_duration=30,
            slot_capacity=5
        )

        self.vaccine_bcg = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="BCG",
            vaccineDescr="Tuberculosis vaccine",
            price=150,
            stock_quantity=50
        )

        self.vaccine_mmr = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="MMR",
            vaccineDescr="Measles, Mumps, Rubella vaccine",
            price=300,
            stock_quantity=40
        )

        self.vaccine_opv = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="OPV",
            vaccineDescr="Oral Polio Vaccine",
            price=0,
            stock_quantity=100
        )

        self.client = Client()

    # -----------------------------------------------------------------------
    # TEST 1: Vaccine Information Queries
    # -----------------------------------------------------------------------
    def test_01_vaccine_information_queries(self):
        # Query 1: MMR
        res_mmr = process_ai_message(patient_id=self.patient.id, message="What is MMR vaccine?")
        self.assertIn("MR / MMR Vaccine", res_mmr['text'])
        self.assertIn("Protects Against", res_mmr['text'])
        self.assertIn("Measles", res_mmr['text'])
        self.assertIn("Medical Disclaimer", res_mmr['text'])

        # Query 2: Polio
        res_polio = process_ai_message(patient_id=self.patient.id, message="What does the polio vaccine prevent?")
        self.assertIn("Polio", res_polio['text'])
        self.assertIn("paralysis", res_polio['text'].lower())

        # Query 3: Hepatitis B
        res_hepb = process_ai_message(patient_id=self.patient.id, message="Why is Hepatitis B vaccine given?")
        self.assertIn("Hepatitis B", res_hepb['text'])
        self.assertIn("liver", res_hepb['text'].lower())

        # Query 4: BCG
        res_bcg = process_ai_message(patient_id=self.patient.id, message="What is BCG?")
        self.assertIn("BCG", res_bcg['text'])
        self.assertIn("Tuberculosis", res_bcg['text'])

    # -----------------------------------------------------------------------
    # TEST 2: Child Vaccination Guidance (Milestone & Registered History)
    # -----------------------------------------------------------------------
    def test_02_child_vaccination_guidance(self):
        # Age-based question (e.g. 9 months old)
        res_age = process_ai_message(
            patient_id=None,
            message="My child is 9 months old. What vaccine is coming next?"
        )
        self.assertIn("Personalized Vaccination Recommendation", res_age['text'])
        self.assertIn("9 Months", res_age['text'])
        self.assertTrue("MR-1" in res_age['text'] or "MR" in res_age['text'] or "PCV" in res_age['text'])
        self.assertIn("Medical Disclaimer", res_age['text'])

        # Logged-in patient question for registered child
        res_child = process_ai_message(
            patient_id=self.patient.id,
            message="What vaccines are upcoming for my child?"
        )
        self.assertIn("Immunization Schedule Analysis", res_child['text'])
        self.assertIn("Aarav", res_child['text'])
        self.assertIn("Due / Recommended", res_child['text'])

    # -----------------------------------------------------------------------
    # TEST 3: Starting Appointment Conversation
    # -----------------------------------------------------------------------
    def test_03_start_appointment_conversation(self):
        res = process_ai_message(patient_id=self.patient.id, message="Book a vaccination appointment.")
        # Patient with 1 child auto-selects child and asks for Hospital
        self.assertEqual(res['context']['booking_ctx']['child_name'], "Aarav")
        self.assertEqual(res['context']['booking_step'], "AWAITING_HOSPITAL")
        self.assertEqual(res['action_type'], "SHOW_HOSPITALS")
        self.assertTrue(any(h['title'] == "City Care Pediatric Hospital" for h in res['action_data']['hospitals']))



    # -----------------------------------------------------------------------
    # TEST 4: Natural Language Booking with Entities ("Book MMR for my child")
    # -----------------------------------------------------------------------
    def test_04_book_mmr_entity_extraction(self):
        res = process_ai_message(patient_id=self.patient.id, message="Book MMR for my child.")
        ctx = res['context']['booking_ctx']
        self.assertEqual(ctx['child_name'], "Aarav")
        self.assertEqual(ctx['vaccine_key'], "mmr")
        self.assertEqual(res['context']['booking_step'], "AWAITING_HOSPITAL")

    # -----------------------------------------------------------------------
    # TEST 5: Hospital Selection
    # -----------------------------------------------------------------------
    def test_05_select_hospital(self):
        context = {
            'booking_step': 'AWAITING_HOSPITAL',
            'booking_ctx': {'child_id': self.child.id, 'child_name': self.child.childname, 'vaccine_key': 'mmr'}
        }
        res = process_ai_message(
            patient_id=self.patient.id,
            message="City Care Pediatric Hospital",
            context=context
        )
        self.assertEqual(res['context']['booking_ctx']['hospital_id'], self.hospital.id)
        self.assertEqual(res['context']['booking_step'], "AWAITING_DATE")

    # -----------------------------------------------------------------------
    # TEST 6: Vaccine Selection
    # -----------------------------------------------------------------------
    def test_06_select_vaccine(self):
        context = {
            'booking_step': 'AWAITING_VACCINE',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname,
                'hospital_id': self.hospital.id,
                'hospital_name': self.hospital.title
            }
        }
        res = process_ai_message(patient_id=self.patient.id, message="MMR", context=context)
        self.assertEqual(res['context']['booking_ctx']['vaccine_id'], self.vaccine_mmr.id)
        self.assertEqual(res['context']['booking_step'], "AWAITING_DATE")

    # -----------------------------------------------------------------------
    # TEST 7: Select Date & Available Slots
    # -----------------------------------------------------------------------
    def test_07_select_date_and_slots(self):
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        context = {
            'booking_step': 'AWAITING_DATE',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname,
                'hospital_id': self.hospital.id,
                'hospital_name': self.hospital.title,
                'vaccine_id': self.vaccine_mmr.id,
                'vaccine_name': self.vaccine_mmr.vaccineName
            }
        }
        res = process_ai_message(patient_id=self.patient.id, message=tomorrow, context=context)
        self.assertEqual(res['context']['booking_step'], "AWAITING_SLOT")
        self.assertEqual(res['action_type'], "SHOW_SLOTS")
        self.assertTrue(len(res['action_data']['slots']) > 0)

    # -----------------------------------------------------------------------
    # TEST 8: Confirm Booking & Validate Appointment Record
    # -----------------------------------------------------------------------
    def test_08_confirm_booking_creates_appointment(self):
        apt_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        context = {
            'booking_step': 'AWAITING_CONFIRMATION',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname,
                'hospital_id': self.hospital.id,
                'hospital_name': self.hospital.title,
                'vaccine_id': self.vaccine_mmr.id,
                'vaccine_name': self.vaccine_mmr.vaccineName,
                'apt_date': apt_date,
                'apt_time': '10:30:00',
                'apt_time_str': '10:30 AM'
            }
        }
        res = process_ai_message(patient_id=self.patient.id, message="Confirm", context=context)
        self.assertEqual(res['action_type'], "BOOKING_SUCCESS")
        self.assertIn("Successfully Confirmed", res['text'])

        # Verify in database
        apt = Appointmenttbl.objects.filter(
            child=self.child,
            vaccineid=self.vaccine_mmr,
            hospitalid=self.hospital
        ).first()
        self.assertIsNotNone(apt)
        self.assertEqual(apt.active, 0) # Booked / Pending
        self.assertEqual(apt.aptdate.strftime('%Y-%m-%d'), apt_date)
        self.assertEqual(apt.apttime, datetime.time(10, 30))

    # -----------------------------------------------------------------------
    # TEST 9: Invalid Inputs & Error Handling
    # -----------------------------------------------------------------------
    def test_09_invalid_inputs_handling(self):
        # 9a. Unknown / invalid hospital
        context_hosp = {
            'booking_step': 'AWAITING_HOSPITAL',
            'booking_ctx': {'child_id': self.child.id, 'child_name': self.child.childname}
        }
        res_hosp = process_ai_message(patient_id=self.patient.id, message="NonExistentHospitalXYZ", context=context_hosp)
        self.assertIn("couldn't find a hospital", res_hosp['text'])
        self.assertEqual(res_hosp['action_type'], 'SHOW_HOSPITALS')

        # 9b. Invalid past date
        context_date = {
            'booking_step': 'AWAITING_DATE',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname,
                'hospital_id': self.hospital.id,
                'hospital_name': self.hospital.title,
                'vaccine_id': self.vaccine_mmr.id
            }
        }
        res_past = process_ai_message(patient_id=self.patient.id, message="2020-01-01", context=context_date)
        self.assertIn("in the past", res_past['text'])


        # 9c. Acute medical symptom query
        res_symptom = process_ai_message(patient_id=self.patient.id, message="My child has high fever above 103, should I give vaccine?")
        self.assertTrue(res_symptom['is_safety_disclaimer'])
        self.assertIn("Important Medical Safety Notice", res_symptom['text'])
        self.assertIn("consult your pediatrician", res_symptom['text'].lower())

    # -----------------------------------------------------------------------
    # TEST 10: Existing Manual Appointment Booking Non-Regression
    # -----------------------------------------------------------------------
    def test_10_existing_manual_booking_still_works(self):
        session = self.client.session
        session['CName'] = self.patient.name
        session['Cid'] = self.patient.id
        session['user_role'] = 'patient'
        session.save()

        # Test GET manual booking page
        response_get = self.client.get(reverse('patient:vaccinebooking'))
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "City Care Pediatric Hospital")

        # Test POST manual booking
        booking_date = (datetime.date.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        response_post = self.client.post(reverse('patient:vaccinebooking'), {
            'hospitalid': self.hospital.id,
            'vaccineid': self.vaccine_bcg.id,
            'child_id': self.child.id,
            'childname': self.child.childname,
            'aptdate': booking_date,
            'apttime': '11:00:00'
        }, follow=True)

        self.assertEqual(response_post.status_code, 200)
        manual_apt = Appointmenttbl.objects.filter(
            child=self.child,
            vaccineid=self.vaccine_bcg,
            hospitalid=self.hospital
        ).first()
        self.assertIsNotNone(manual_apt)
        self.assertEqual(manual_apt.active, 0)

    # -----------------------------------------------------------------------
    # TEST 11: HTTP Endpoint for AI Assistant
    # -----------------------------------------------------------------------
    def test_11_ai_assistant_http_endpoint(self):
        session = self.client.session
        session['CName'] = self.patient.name
        session['Cid'] = self.patient.id
        session['user_role'] = 'patient'
        session.save()

        # POST JSON to /ai-assistant/chat/
        response = self.client.post(
            reverse('patient:ai_assistant_chat'),
            data={'message': 'What is PCV?'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Pneumococcal", data['text'])
        self.assertIn("Medical Disclaimer", data['text'])

    # -----------------------------------------------------------------------
    # TEST 12: Precise Hospital Selection with Similar Names (e.g. UPHC facilities)
    # -----------------------------------------------------------------------
    def test_12_precise_hospital_selection_with_common_names(self):
        # Create multiple hospitals sharing common generic terms
        hosp_alkapuri = Hospitaltbl.objects.create(
            title="Alkapuri UPHC Clinic",
            address="Alkapuri, Vadodara",
            cityId=self.city,
            areaId=self.area,
            contactNo=9111111111,
            password="pass"
        )
        hosp_tarsali = Hospitaltbl.objects.create(
            title="Tarsali UPHC Clinic",
            address="Tarsali, Vadodara",
            cityId=self.city,
            areaId=self.area,
            contactNo=9222222222,
            password="pass"
        )

        context = {
            'booking_step': 'AWAITING_HOSPITAL',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname
            }
        }

        # Select "Tarsali UPHC Clinic"
        res = process_ai_message(patient_id=self.patient.id, message="Tarsali UPHC Clinic", context=context)
        self.assertEqual(res['context']['booking_ctx']['hospital_id'], hosp_tarsali.id)
        self.assertEqual(res['context']['booking_ctx']['hospital_name'], "Tarsali UPHC Clinic")
        self.assertIn("Tarsali UPHC Clinic", res['text'])
        self.assertNotIn("Alkapuri UPHC Clinic", res['text'])

        # Select "Alkapuri UPHC Clinic"
        context_alk = {
            'booking_step': 'AWAITING_HOSPITAL',
            'booking_ctx': {
                'child_id': self.child.id,
                'child_name': self.child.childname
            }
        }
        res_alk = process_ai_message(patient_id=self.patient.id, message="Alkapuri UPHC Clinic", context=context_alk)
        self.assertEqual(res_alk['context']['booking_ctx']['hospital_id'], hosp_alkapuri.id)
        self.assertEqual(res_alk['context']['booking_ctx']['hospital_name'], "Alkapuri UPHC Clinic")
        self.assertIn("Alkapuri UPHC Clinic", res_alk['text'])
        self.assertNotIn("Tarsali UPHC Clinic", res_alk['text'])

