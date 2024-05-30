from django.db import models
from adminapp.models import City,Area
from hospitalapp.models import Hospitaltbl,Vaccinetbl


# Create your models here.
class Patienttbl(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.IntegerField(blank=True, null=True,verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
   
    def __str__(self):
        return f'{(self.name)(self.pk)}'
    
class Appointmenttbl(models.Model):
    hospitalid = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, verbose_name="Title")    
    vaccineid = models.ForeignKey(Vaccinetbl, on_delete=models.CASCADE, verbose_name="Vaccine")  
    patientid = models.ForeignKey(Patienttbl,blank=True, null=True, on_delete=models.CASCADE, verbose_name="Name")    
    childname = models.CharField(max_length=255,blank=True, null=True,verbose_name="Child Name" )
    aptdate  = models.DateField(null=True,verbose_name="Appointment Date")
    indt  = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    outdt  = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    active = models.IntegerField(blank=True, null=True)   
    rfidno  = models.IntegerField(blank=True, null=True)
   
    def __str__(self):
        return f'{(self.hospitalid)(self.vaccineid)(self.patientid)(self.hospitalid.title)(self.vaccineid.vaccineName)(self.patientid.name)(self.aptdate)(self.active)(self.pk)}'