import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from patientapp.models import Patienttbl, Childtbl, Appointmenttbl, Notification
from hospitalapp.models import Hospitaltbl, Vaccinetbl
from adminapp.models import City, Area
from patientapp.services.notification_service import (
    get_patient_notifications,
    generate_ai_insight,
    mark_patient_notifications_read,
)


class NotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(cityName="Surat")
        self.area = Area.objects.create(cityId=self.city, areaName="Adajan")

        self.parent = Patienttbl.objects.create(
            name="Ramesh Patel",
            address="Ring Road",
            cityId=self.city,
            areaId=self.area,
            contactNo=9998887776,
            password="pass123Patel",
            pincode="395009",
            account_status="ACTIVE",
            must_change_password=False
        )

        self.hospital = Hospitaltbl.objects.create(
            title="City Care Hospital",
            address="Adajan Main Road",
            cityId=self.city,
            areaId=self.area,
            contactNo=9876543210,
            password="hosp_pass_123",
            pincode="395009"
        )

        self.vaccine_bcg = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="BCG",
            vaccineDescr="Tuberculosis vaccine",
            price=200,
            stock_quantity=20,
            minimum_quantity=5
        )

        self.vaccine_penta = Vaccinetbl.objects.create(
            hospitalId=self.hospital,
            vaccineName="Pentavalent-1",
            vaccineDescr="5-in-1 vaccine",
            price=500,
            stock_quantity=15,
            minimum_quantity=5
        )

        self.child = Childtbl.objects.create(
            patient=self.parent,
            childname="Aarav Patel",
            dob=datetime.date.today() - datetime.timedelta(days=60),
            gender="Boy",
            blood_group="O+"
        )

    def test_ai_insight_generation(self):
        insight_imminent = generate_ai_insight('imminent', 'BCG', 'Aarav')
        self.assertIn("BCG", insight_imminent)
        self.assertIn("small red bump", insight_imminent)

        insight_delayed = generate_ai_insight('delayed', 'Pentavalent-1', 'Aarav')
        self.assertIn("Catch-up", insight_delayed)

        insight_completed = generate_ai_insight('completed', 'Pentavalent-1', 'Aarav')
        self.assertIn("cool, damp cloth", insight_completed)

    def test_upcoming_and_delayed_appointment_notifications(self):
        today = datetime.date.today()

        # 1. Upcoming appointment (Tomorrow)
        apt_upcoming = Appointmenttbl.objects.create(
            patientid=self.parent,
            child=self.child,
            childname=self.child.childname,
            hospitalid=self.hospital,
            vaccineid=self.vaccine_bcg,
            aptdate=today + datetime.timedelta(days=1),
            apttime=datetime.time(10, 30),
            active=Appointmenttbl.STATUS_BOOKED
        )

        # 2. Delayed appointment (Past date)
        apt_delayed = Appointmenttbl.objects.create(
            patientid=self.parent,
            child=self.child,
            childname=self.child.childname,
            hospitalid=self.hospital,
            vaccineid=self.vaccine_penta,
            aptdate=today - datetime.timedelta(days=5),
            apttime=datetime.time(11, 0),
            active=Appointmenttbl.STATUS_BOOKED
        )

        # 3. Completed appointment
        apt_completed = Appointmenttbl.objects.create(
            patientid=self.parent,
            child=self.child,
            childname=self.child.childname,
            hospitalid=self.hospital,
            vaccineid=self.vaccine_bcg,
            aptdate=today - datetime.timedelta(days=20),
            apttime=datetime.time(9, 0),
            active=Appointmenttbl.STATUS_COMPLETED
        )

        res = get_patient_notifications(self.parent.id)
        notifs = res.get('notifications', [])
        stats = res.get('stats', {})

        self.assertGreaterEqual(len(notifs), 3)
        self.assertGreaterEqual(stats.get('upcoming', 0), 1)
        self.assertGreaterEqual(stats.get('delayed', 0), 1)
        self.assertGreaterEqual(stats.get('completed', 0), 1)

        # Find upcoming notification
        upcoming_item = next(n for n in notifs if n.get('appointment_id') == apt_upcoming.id)
        self.assertEqual(upcoming_item['category'], 'upcoming')
        self.assertEqual(upcoming_item['badge_label'], 'TOMORROW')
        self.assertIn('Aarav', upcoming_item['title'])
        self.assertIn('AI', upcoming_item['ai_insight'])

        # Find delayed notification
        delayed_item = next(n for n in notifs if n.get('appointment_id') == apt_delayed.id)
        self.assertEqual(delayed_item['category'], 'delayed')
        self.assertIn('OVERDUE', delayed_item['badge_label'])
        self.assertEqual(delayed_item['action_label'], 'Reschedule Now')

    def test_get_notifications_view_unauthenticated(self):
        url = reverse('patient:get_notifications')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get('success', True))
        self.assertEqual(data.get('unread_count'), 0)

    def test_get_notifications_view_authenticated(self):
        # Set session
        session = self.client.session
        session['Cid'] = self.parent.id
        session['CName'] = self.parent.name
        session.save()

        # Create upcoming appointment
        today = datetime.date.today()
        Appointmenttbl.objects.create(
            patientid=self.parent,
            child=self.child,
            hospitalid=self.hospital,
            vaccineid=self.vaccine_bcg,
            aptdate=today,
            apttime=datetime.time(14, 0),
            active=Appointmenttbl.STATUS_BOOKED
        )

        url = reverse('patient:get_notifications')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertGreater(len(data.get('notifications', [])), 0)

    def test_mark_notifications_read(self):
        session = self.client.session
        session['Cid'] = self.parent.id
        session.save()

        # Create unread db notification
        Notification.objects.create(
            patient=self.parent,
            message="Test unread alert",
            notification_type="appointment",
            is_read=False
        )

        url = reverse('patient:mark_notifications_read')
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('success'))

        # Check DB notification is read
        unread_cnt = Notification.objects.filter(patient=self.parent, is_read=False).count()
        self.assertEqual(unread_cnt, 0)
