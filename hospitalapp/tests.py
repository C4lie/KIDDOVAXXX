import datetime
from django.test import TestCase
from django.urls import reverse
from hospitalapp.models import Hospitaltbl, Receptionisttbl
from hospitalapp.views import generate_ui_number
from adminapp.models import City, Area
from patientapp.models import Patienttbl, RFIDCard
from patientapp.services.hospital_registration_service import verify_patient_registration_by_phone


class HospitalStaffUiNumberTestCase(TestCase):
    def setUp(self):
        self.city = City.objects.create(cityName='Test City')
        self.area = Area.objects.create(areaName='Test Area', cityId=self.city)
        self.hospital = Hospitaltbl.objects.create(
            title='Test Hospital',
            address='Test Address',
            cityId=self.city,
            areaId=self.area,
            contactNo=1234567890,
            password='secret'
        )

    def test_generate_ui_number_is_five_digit_numeric(self):
        code = generate_ui_number()
        self.assertEqual(len(code), 5)
        self.assertTrue(code.isdigit())

    def test_staff_ui_number_can_be_persisted(self):
        code = generate_ui_number()
        staff = Receptionisttbl.objects.create(
            hospitalid=self.hospital,
            name='Apex Staff',
            address='Street 1',
            gender='Male',
            cityId=self.city,
            areaId=self.area,
            contactNo=9090909090,
            ui_no=code,
            password='staffpass',
            staffimg='',
            doj=datetime.date.today(),
        )

        self.assertEqual(staff.ui_no, code)
        self.assertEqual(len(staff.ui_no), 5)

    def test_patient_registration_template_can_render_for_hospital_staff(self):
        session = self.client.session
        session['CName'] = 'Apex Staff'
        session['Cid'] = self.hospital.id
        session.save()

        response = self.client.get(reverse('hospitalapp:patient_registration'))
        self.assertEqual(response.status_code, 200)

    def test_verify_patient_registration_by_phone_confirms_pending_portal(self):
        patient = Patienttbl.objects.create(
            name='Phone Verified Parent',
            address='Test Lane',
            cityId=self.area.cityId,
            areaId=self.area,
            contactNo=9876543210,
            password='secret',
            relation='Parent',
            account_status='RFID_ASSIGNED',
            must_change_password=True,
            registered_hospital=self.hospital,
        )

        RFIDCard.objects.create(
            card_number='99990001',
            patient=patient,
            is_active=True,
            assigned_by_hospital=self.hospital,
            assigned_by_staff='Apex Staff',
        )

        result = verify_patient_registration_by_phone(
            patient_id=patient.id,
            phone_number='9876543210',
            staff_name='Apex Staff',
        )

        self.assertTrue(result['success'])
        patient.refresh_from_db()
        self.assertEqual(patient.account_status, 'ACTIVE')
        self.assertTrue(patient.must_change_password)

