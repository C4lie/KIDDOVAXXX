import os
import django
from adminapp.models import Admintbl, City, Area
from hospitalapp.models import Hospitaltbl, Receptionisttbl
import datetime

if not Admintbl.objects.filter(username='admin').exists():
    Admintbl.objects.create(username='admin', password='admin')
else:
    Admintbl.objects.filter(username='admin').update(password='admin')

city, _ = City.objects.get_or_create(cityName='DummyCity')
area, _ = Area.objects.get_or_create(areaName='DummyArea', cityId=city)

if not Hospitaltbl.objects.filter(contactNo=1).exists():
    h = Hospitaltbl.objects.create(title='Dummy Hospital', address='Dummy Address', cityId=city, areaId=area, contactNo=1, password='hospital')
else:
    h = Hospitaltbl.objects.get(contactNo=1)
    h.password = 'hospital'
    h.save()

if not Receptionisttbl.objects.filter(contactNo=2).exists():
    Receptionisttbl.objects.create(hospitalid=h, name='Receptionist', address='Dummy Address', gender='Male', cityId=city, areaId=area, contactNo=2, password='receptionist', doj=datetime.date.today())
else:
    r = Receptionisttbl.objects.get(contactNo=2)
    r.password = 'receptionist'
    r.save()
print('Created users successfully!')
