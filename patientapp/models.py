from django.db import models  # type: ignore[import]  # pyre-ignore
from adminapp.models import City,Area  # type: ignore[import]  # pyre-ignore
from hospitalapp.models import Hospitaltbl,Vaccinetbl  # type: ignore[import]  # pyre-ignore


# Create your models here.
class Patienttbl(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.IntegerField(blank=True, null=True,verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
    relation = models.CharField(max_length=50, blank=True, null=True, verbose_name="Relation")
   
    def __str__(self):
        return f'{(self.name)(self.pk)}'
    
class Appointmenttbl(models.Model):
    hospitalid = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, verbose_name="Title")    
    vaccineid = models.ForeignKey(Vaccinetbl, on_delete=models.CASCADE, verbose_name="Vaccine")  
    patientid = models.ForeignKey(Patienttbl,blank=True, null=True, on_delete=models.CASCADE, verbose_name="Name")    
    childname = models.CharField(max_length=255,blank=True, null=True,verbose_name="Child Name" )
    # New nullable FK — old rows stay NULL, new bookings can carry child reference
    child = models.ForeignKey('Childtbl', blank=True, null=True, on_delete=models.SET_NULL, related_name='appointments', verbose_name="Child Profile")
    aptdate  = models.DateField(null=True,verbose_name="Appointment Date")
    indt  = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    outdt  = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    active = models.IntegerField(blank=True, null=True)   
    rfidno  = models.IntegerField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False, verbose_name="Reminder Sent")
    is_confirmed  = models.BooleanField(default=False, verbose_name="Confirmed by Patient")
   
    def __str__(self):
        return f'{(self.hospitalid)(self.vaccineid)(self.patientid)(self.hospitalid.title)(self.vaccineid.vaccineName)(self.patientid.name)(self.aptdate)(self.active)(self.pk)}'

class Childtbl(models.Model):
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='children', verbose_name="Parent")
    childname = models.CharField(max_length=255, verbose_name="Child Name")
    dob = models.DateField(verbose_name="Date of Birth")
    gender = models.CharField(max_length=50, verbose_name="Gender")
    
    @property
    def age(self):
        import datetime
        today = datetime.date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def __str__(self):
        return self.childname


class VaccinationRecord(models.Model):
    """Immutable record created when a receptionist marks an appointment complete (active=2)."""
    child = models.ForeignKey(Childtbl, on_delete=models.CASCADE, related_name='vaccination_records', verbose_name="Child")
    vaccine = models.ForeignKey('hospitalapp.Vaccinetbl', on_delete=models.CASCADE, verbose_name="Vaccine")
    appointment = models.OneToOneField(Appointmenttbl, on_delete=models.CASCADE, related_name='vaccination_record', verbose_name="Appointment")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('child', 'vaccine')  # prevent same vaccine being recorded twice per child

    def __str__(self):
        return f"{self.child.childname} — {self.vaccine.vaccineName}"


class Notification(models.Model):
    """
    Stores in-app alerts for users and acts as a record to prevent duplicate SMS/reminders.
    - notification_type: 'appointment' or 'vaccine'
    - related_id: appointment.id (for appointments) or child.id (for vaccines)
    """
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='notifications', verbose_name="Patient")
    message = models.TextField(verbose_name="Message")
    notification_type = models.CharField(max_length=50, verbose_name="Type")
    related_id = models.IntegerField(null=True, blank=True, verbose_name="Related ID")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"To {self.patient.name} ({self.notification_type}): {self.message[:50]}"