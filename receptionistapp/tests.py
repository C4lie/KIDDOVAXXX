import datetime
import json
from django.test import TestCase
from django.urls import reverse
from patientapp.models import Patienttbl, Childtbl, Appointmenttbl, RFIDCard
from hospitalapp.models import Hospitaltbl, Vaccinetbl
from adminapp.models import City, Area
from receptionistapp.services.rfid_service import scan_rfid_card, generate_unique_rfid_number, link_rfid_card


class RFIDInfrastructureTestCase(TestCase):
    def setUp(self):
        self.city = City.objects.create(cityName="TestCity")
        self.area = Area.objects.create(areaName="TestArea", cityId=self.city)
        self.hospital = Hospitaltbl.objects.create(
            title="CityCare Hospital",
            address="123 Main St",
            cityId=self.city,
            areaId=self.area,
            password="pass"
        )
        self.vaccine = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="MMR",
            vaccineDescr="Measles, Mumps, Rubella",
            price=500,
            stock_quantity=50,
            minimum_quantity=10
        )
        self.patient = Patienttbl.objects.create(
            name="Aarav Patel",
            address="456 Park Ave",
            cityId=self.city,
            areaId=self.area,
            contactNo=9876543210,
            password="pass"
        )
        self.child = Childtbl.objects.create(
            patient=self.patient,
            childname="Aarav Jr",
            dob=datetime.date(2024, 3, 12),
            gender="Boy"
        )
        self.rfid_card = RFIDCard.objects.create(
            card_number="10384721",
            patient=self.patient
        )

    def test_persistent_rfid_lookup(self):
        result = scan_rfid_card("10384721", hospital_id=self.hospital.id)
        self.assertTrue(result['found'])
        self.assertEqual(result['patient']['name'], "Aarav Patel")
        self.assertEqual(result['child']['name'], "Aarav Jr")

    def test_unknown_rfid_card(self):
        result = scan_rfid_card("99881234")
        self.assertFalse(result['found'])
        self.assertEqual(result['status'], "NOT_REGISTERED")

    def test_generate_unique_rfid_number(self):
        num = generate_unique_rfid_number()
        self.assertEqual(len(num), 8)
        self.assertTrue(num.isdigit())
        self.assertFalse(RFIDCard.objects.filter(card_number=num).exists())

    def test_rfid_generate_api_payload_contract(self):
        response = self.client.get(reverse('receptionist:rfid_generate_api'))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertIn('card_number', payload)
        self.assertIn('rfid', payload)
        self.assertEqual(payload['rfid'], payload['card_number'])

    def test_link_rfid_card(self):
        new_num = "84729103"
        link_result = link_rfid_card(new_num, patient_id=self.patient.id, child_id=self.child.id)
        self.assertTrue(link_result['success'])

        scan_res = scan_rfid_card(new_num)
        self.assertTrue(scan_res['found'])
        self.assertEqual(scan_res['patient']['name'], "Aarav Patel")
