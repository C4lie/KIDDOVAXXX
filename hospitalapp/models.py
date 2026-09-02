from django.db import models
from adminapp.models import City, Area
# Create your models here.
class Hospitaltbl(models.Model):
    title = models.CharField(max_length=500, verbose_name="Title")
    dcrname = models.CharField(max_length=255, blank=True, null=True, default='', verbose_name="Doctor Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.BigIntegerField(blank=True, null=True, verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
    img = models.ImageField(upload_to='profileimg', blank=True, null=True, verbose_name="Profile Image")

    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    opening_time = models.TimeField(default="09:00:00", blank=True, null=True, verbose_name="Opening Time")
    closing_time = models.TimeField(default="17:00:00", blank=True, null=True, verbose_name="Closing Time")
    slot_duration = models.IntegerField(default=30, blank=True, null=True, verbose_name="Slot Duration (mins)")
    slot_capacity = models.IntegerField(default=2, blank=True, null=True, verbose_name="Slot Capacity")

    def HospitalImageUrl(self):
        try:
            if self.img and hasattr(self.img, 'url'):
                return self.img.url
        except Exception:
            pass
        return '/static/profileimg/noimg.png'
     
    def __str__(self):
        return f'{self.title} ({self.pk})'

class HospitalBreak(models.Model):
    hospital = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, related_name='breaks', verbose_name="Hospital")
    start_time = models.TimeField(verbose_name="Start Time")
    end_time = models.TimeField(verbose_name="End Time")

    def __str__(self):
        return f"Break {self.start_time} - {self.end_time} at {self.hospital.title}"

class HospitalHoliday(models.Model):
    hospital = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, related_name='holidays', verbose_name="Hospital")
    date = models.DateField(verbose_name="Closed Date")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return f"Closed on {self.date} at {self.hospital.title}"

class VaccinationRecordAlert(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('VERIFIED', 'Verified by Staff'),
        ('CORRECTED', 'Correction Required'),
    ]

    child = models.ForeignKey('patientapp.Childtbl', on_delete=models.CASCADE, related_name='quality_alerts', verbose_name="Child")
    appointment = models.ForeignKey('patientapp.Appointmenttbl', on_delete=models.CASCADE, blank=True, null=True, related_name='quality_alerts', verbose_name="Appointment")
    vaccine_name = models.CharField(max_length=255, verbose_name="Vaccine Name")
    issue_type = models.CharField(max_length=100, verbose_name="Issue Type")
    severity = models.CharField(max_length=20, verbose_name="Severity") # HIGH, MEDIUM, NORMAL, LOW
    description = models.TextField(verbose_name="Description")
    recommended_action = models.TextField(verbose_name="Recommended Action")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert ({self.severity}): {self.vaccine_name} for {self.child.childname}"

class Vaccinetbl(models.Model):
    hospitalId= models.ForeignKey(Hospitaltbl,null=True,blank=True,on_delete=models.CASCADE)
    vaccineName = models.CharField(max_length=255, verbose_name='Vaccine Name')   
    vaccineDescr = models.CharField(max_length=500, verbose_name='Description') 
    price = models.IntegerField(blank=True, null=True, verbose_name='Price')
    stock_quantity = models.IntegerField(default=50, verbose_name='Stock Quantity')
    minimum_quantity = models.IntegerField(default=5, verbose_name='Minimum Quantity')
    
    def __str__(self):
        return f'{self.vaccineName} - {self.price}'


class VaccineInfo(models.Model):
    vaccine = models.ForeignKey(Vaccinetbl, on_delete=models.CASCADE, related_name='education_info', verbose_name='Vaccine')
    protects_against = models.TextField(verbose_name='Protects Against')
    side_effects = models.TextField(verbose_name='Common Side Effects')
    warning_signs = models.TextField(verbose_name='Warning Signs')

    def __str__(self):
        return f"Info for {self.vaccine.vaccineName}"

    
class Receptionisttbl(models.Model):
    hospitalid = models.ForeignKey(Hospitaltbl,blank=True, null=True, on_delete=models.CASCADE, verbose_name="Title")    
    name = models.CharField(max_length=255, verbose_name="Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    gender= models.CharField(default='Male',max_length=10, verbose_name="Gender")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.BigIntegerField(blank=True, null=True, verbose_name="Contact")
    ui_no = models.CharField(max_length=5, unique=True, blank=True, null=True, verbose_name="UI Number")
    password = models.CharField(max_length=255, verbose_name="Password")
    staffimg = models.ImageField(verbose_name="Upload Image", upload_to='staffimages', blank=True, null=True)
    doj = models.DateField(null=True, blank=True, verbose_name="DateofJoining")

    def StaffImageUrl(self):
        try:
            if self.staffimg and hasattr(self.staffimg, 'url'):
                return self.staffimg.url
        except Exception:
            pass
        return '/static/staffimages/noimg.png'
    
    def __str__(self):
        return f'{self.name} ({self.ui_no or self.pk})'