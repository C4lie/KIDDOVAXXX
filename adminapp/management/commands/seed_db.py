import os
import csv
from datetime import date
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.hashers import make_password
from adminapp.models import Admintbl, City, Area
from hospitalapp.models import Hospitaltbl, Vaccinetbl, Receptionisttbl

class Command(BaseCommand):
    help = "Seed initial production data (Admintbl, City, Area, Hospitals, Receptionists, UIP Vaccines)"

    def handle(self, *args, **options):
        # 1. Seed Admin
        admin_user, created = Admintbl.objects.get_or_create(
            username='admin',
            defaults={'password': make_password('admin')}
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created default admin user ('admin')."))

        # 2. Seed Vadodara & Areas
        city_obj, _ = City.objects.get_or_create(cityName='Vadodara')
        
        areas = ['Alkapuri', 'Chhani', 'Nizampura', 'Fatehgunj', 'Manjalpur', 'Tarsali', 'Waghodia', 'Vrundavan', 'Ajwa', 'Harni']
        for a_name in areas:
            Area.objects.get_or_create(areaName=a_name, cityId=city_obj)

        self.stdout.write(self.style.SUCCESS(f"Seeded City '{city_obj.cityName}' and {len(areas)} areas."))

        # 3. Seed Hospitals & Receptionists from CSV if present
        csv_path = os.path.join(settings.BASE_DIR, 'vadodara_hospital_registration_details.csv')
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                h_count = 0
                for row in reader:
                    c_name = row.get('City', 'Vadodara').strip() or 'Vadodara'
                    a_name = row.get('Area', 'Alkapuri').strip() or 'Alkapuri'
                    title = row.get('Title', '').strip()
                    doctor_name = row.get('Doctor Name', '').strip()
                    address = row.get('Address', '').strip()
                    contact_str = row.get('Contact', '').strip()
                    password_str = row.get('Password', '').strip()

                    if not title or not contact_str:
                        continue

                    try:
                        contact_no = int(contact_str)
                    except ValueError:
                        continue

                    c_item, _ = City.objects.get_or_create(cityName=c_name)
                    a_item, _ = Area.objects.get_or_create(areaName=a_name, cityId=c_item)

                    h_obj, h_created = Hospitaltbl.objects.get_or_create(
                        contactNo=contact_no,
                        defaults={
                            'title': title,
                            'dcrname': doctor_name,
                            'address': address,
                            'cityId': c_item,
                            'areaId': a_item,
                            'password': make_password(password_str) if password_str else make_password('hospital'),
                        }
                    )
                    if h_created:
                        h_count += 1
                        # Create default receptionist
                        ui_no = f"R{h_obj.id:03d}"
                        Receptionisttbl.objects.get_or_create(
                            hospitalid=h_obj,
                            defaults={
                                'name': f"Staff - {h_obj.title}",
                                'address': h_obj.address,
                                'gender': 'Female',
                                'cityId': c_item,
                                'areaId': a_item,
                                'contactNo': contact_no,
                                'ui_no': ui_no,
                                'password': make_password(password_str) if password_str else make_password('receptionist'),
                                'doj': date.today(),
                            }
                        )

                        # Seed 29 standard UIP vaccines
                        UIP_VACCINES = [
                            {"name": "BCG", "descr": "At birth — Birth dose for Tuberculosis", "price": 0, "stock": 50},
                            {"name": "Hepatitis B (Birth Dose)", "descr": "At birth — Birth dose within 24 hours for Hepatitis B", "price": 0, "stock": 50},
                            {"name": "OPV-0", "descr": "At birth — Birth dose Oral Polio Vaccine", "price": 0, "stock": 50},
                            {"name": "OPV-1", "descr": "6 weeks — 1st dose Oral Polio Vaccine", "price": 0, "stock": 45},
                            {"name": "Pentavalent-1", "descr": "6 weeks — 1st dose (DTP + HepB + Hib)", "price": 150, "stock": 40},
                            {"name": "Rotavirus-1", "descr": "6 weeks — 1st dose Rotavirus Vaccine", "price": 200, "stock": 40},
                            {"name": "fIPV-1", "descr": "6 weeks — 1st Fractional Inactivated Polio Vaccine", "price": 100, "stock": 40},
                            {"name": "PCV-1", "descr": "6 weeks — 1st Pneumococcal Conjugate Vaccine", "price": 250, "stock": 40},
                            {"name": "OPV-2", "descr": "10 weeks — 2nd dose Oral Polio Vaccine", "price": 0, "stock": 45},
                            {"name": "Pentavalent-2", "descr": "10 weeks — 2nd dose (DTP + HepB + Hib)", "price": 150, "stock": 40},
                            {"name": "Rotavirus-2", "descr": "10 weeks — 2nd dose Rotavirus Vaccine", "price": 200, "stock": 40},
                            {"name": "OPV-3", "descr": "14 weeks — 3rd dose Oral Polio Vaccine", "price": 0, "stock": 45},
                            {"name": "Pentavalent-3", "descr": "14 weeks — 3rd dose (DTP + HepB + Hib)", "price": 150, "stock": 40},
                            {"name": "Rotavirus-3", "descr": "14 weeks — 3rd dose Rotavirus Vaccine", "price": 200, "stock": 40},
                            {"name": "fIPV-2", "descr": "14 weeks — 2nd Fractional Inactivated Polio Vaccine", "price": 100, "stock": 40},
                            {"name": "PCV-2", "descr": "14 weeks — 2nd Pneumococcal Conjugate Vaccine", "price": 250, "stock": 40},
                            {"name": "MR-1", "descr": "9–12 months — 1st Measles-Rubella Vaccine", "price": 250, "stock": 35},
                            {"name": "PCV Booster", "descr": "9–12 months — Pneumococcal Booster", "price": 300, "stock": 35},
                            {"name": "fIPV-3", "descr": "9–12 months — 3rd Fractional Inactivated Polio Vaccine", "price": 100, "stock": 35},
                            {"name": "JE-1", "descr": "9–12 months — 1st Japanese Encephalitis Vaccine", "price": 350, "stock": 30},
                            {"name": "Vitamin A (1st Dose)", "descr": "9 months — 1st Vitamin A Supplementation", "price": 50, "stock": 50},
                            {"name": "MR-2", "descr": "16–24 months — 2nd Measles-Rubella Vaccine", "price": 250, "stock": 35},
                            {"name": "DPT Booster-1", "descr": "16–24 months — 1st DPT Booster", "price": 300, "stock": 35},
                            {"name": "OPV Booster", "descr": "16–24 months — Oral Polio Booster", "price": 0, "stock": 45},
                            {"name": "JE-2", "descr": "16–24 months — 2nd Japanese Encephalitis Vaccine", "price": 350, "stock": 30},
                            {"name": "Vitamin A (Bi-annual)", "descr": "16–24 months onward — Every 6 months up to 5 years", "price": 50, "stock": 50},
                            {"name": "DPT Booster-2", "descr": "5–6 years — 2nd DPT Booster", "price": 300, "stock": 35},
                            {"name": "Td (10 Years)", "descr": "10 years — Tetanus & Adult Diphtheria", "price": 100, "stock": 35},
                            {"name": "Td (16 Years)", "descr": "16 years — Tetanus & Adult Diphtheria", "price": 100, "stock": 35},
                        ]
                        for v_data in UIP_VACCINES:
                            Vaccinetbl.objects.get_or_create(
                                hospitalId=h_obj,
                                vaccineName=v_data['name'],
                                defaults={
                                    'vaccineDescr': v_data['descr'],
                                    'price': v_data['price'],
                                    'stock_quantity': v_data['stock'],
                                    'minimum_quantity': 5
                                }
                            )
                self.stdout.write(self.style.SUCCESS(f"Seeded {h_count} hospitals with receptionists and UIP vaccines."))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
