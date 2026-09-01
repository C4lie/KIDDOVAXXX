import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiddovax.settings')
django.setup()

from adminapp.models import Admintbl, City, Area
from hospitalapp.models import Hospitaltbl, Receptionisttbl
import datetime
from django.contrib.auth.hashers import make_password

Admintbl.objects.update_or_create(
    username='admin',
    defaults={'password': make_password('admin')}
)

city, _ = City.objects.get_or_create(cityName='Vadodara')
area, _ = Area.objects.get_or_create(areaName='Alkapuri', cityId=city)

h, _ = Hospitaltbl.objects.update_or_create(
    contactNo=1,
    defaults={
        'title': 'Dummy Hospital',
        'address': 'Dummy Address',
        'cityId': city,
        'areaId': area,
        'password': make_password('hospital'),
    }
)

Receptionisttbl.objects.update_or_create(
    contactNo=2,
    defaults={
        'hospitalid': h,
        'name': 'Receptionist',
        'address': 'Dummy Address',
        'gender': 'Male',
        'cityId': city,
        'areaId': area,
        'password': make_password('receptionist'),
        'doj': datetime.date.today()
    }
)
