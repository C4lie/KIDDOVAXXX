from django.db import models  # type: ignore[import]  # pyre-ignore
from adminapp.models import City,Area  # type: ignore[import]  # pyre-ignore
from hospitalapp.models import Hospitaltbl,Vaccinetbl,Receptionisttbl  # type: ignore[import]  # pyre-ignore


# Create your models here.
class Patienttbl(models.Model):
    ACCOUNT_STATUS_CHOICES = [
        ('PENDING_HOSPITAL_REGISTRATION', 'Pending Hospital Registration'),
        ('RFID_ASSIGNED', 'RFID Assigned'),
        ('ACTIVE', 'Active'),
    ]

    name = models.CharField(max_length=255, verbose_name="Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.IntegerField(blank=True, null=True,verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
    relation = models.CharField(max_length=50, blank=True, null=True, verbose_name="Relation")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")

    # Account lifecycle fields
    account_status = models.CharField(
        max_length=30, choices=ACCOUNT_STATUS_CHOICES,
        default='PENDING_HOSPITAL_REGISTRATION', verbose_name="Account Status"
    )
    must_change_password = models.BooleanField(default=True, verbose_name="Must Change Password")
    registered_hospital = models.ForeignKey(
        Hospitaltbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='registered_patients', verbose_name="Registration Hospital"
    )

    def __str__(self):
        return f'{self.name} ({self.pk})'
    
class Appointmenttbl(models.Model):
    """
    Appointment status lifecycle (active field):
        0 = BOOKED
        1 = CHECKED_IN (after first RFID scan)
        2 = VERIFIED (receptionist verified identity & appointment)
        3 = VACCINATION_IN_PROGRESS (sent to vaccination room)
        4 = COMPLETED (after second RFID scan & vaccination confirmation)
        5 = CANCELLED
    """
    STATUS_BOOKED = 0
    STATUS_CHECKED_IN = 1
    STATUS_VERIFIED = 2
    STATUS_VACCINATION_IN_PROGRESS = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    hospitalid = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, verbose_name="Title")    
    vaccineid = models.ForeignKey(Vaccinetbl, on_delete=models.CASCADE, verbose_name="Vaccine")  
    patientid = models.ForeignKey(Patienttbl,blank=True, null=True, on_delete=models.CASCADE, verbose_name="Name")    
    childname = models.CharField(max_length=255,blank=True, null=True,verbose_name="Child Name" )
    # New nullable FK — old rows stay NULL, new bookings can carry child reference
    child = models.ForeignKey('Childtbl', blank=True, null=True, on_delete=models.SET_NULL, related_name='appointments', verbose_name="Child Profile")
    aptdate  = models.DateField(null=True,verbose_name="Appointment Date")
    apttime  = models.TimeField(null=True, blank=True, verbose_name="Appointment Time")
    indt  = models.DateTimeField(blank=True, null=True)
    outdt  = models.DateTimeField(blank=True, null=True)
    active = models.IntegerField(blank=True, null=True, default=0)   
    rfidno  = models.IntegerField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False, verbose_name="Reminder Sent")
    is_confirmed  = models.BooleanField(default=False, verbose_name="Confirmed by Patient")

    # RFID transaction tracking fields
    checkin_rfid = models.CharField(max_length=100, blank=True, null=True, verbose_name="Check-in RFID")
    checkin_receptionist = models.ForeignKey(
        Receptionisttbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='checkin_appointments', verbose_name="Check-in Receptionist"
    )
    checkin_time = models.DateTimeField(null=True, blank=True, verbose_name="Check-in Time")
    completion_rfid = models.CharField(max_length=100, blank=True, null=True, verbose_name="Completion RFID")
    completion_receptionist = models.ForeignKey(
        Receptionisttbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='completion_appointments', verbose_name="Completion Receptionist"
    )
    completion_time = models.DateTimeField(null=True, blank=True, verbose_name="Completion Time")
    queue_position = models.IntegerField(null=True, blank=True, verbose_name="Queue Position")

    @property
    def display_child_name(self):
        if self.childname:
            return self.childname
        if self.child and hasattr(self.child, 'childname') and self.child.childname:
            return self.child.childname
        return "Child Profile"

    @property
    def status_label(self):
        """Human-readable status label."""
        labels = {
            0: 'BOOKED', 1: 'CHECKED_IN', 2: 'VERIFIED',
            3: 'VACCINATION_IN_PROGRESS', 4: 'COMPLETED', 5: 'CANCELLED'
        }
        return labels.get(self.active, 'UNKNOWN')

    def __str__(self):
        return f'Appointment #{self.pk} — {self.childname or ""} at {self.hospitalid.title if self.hospitalid else ""}'

class Childtbl(models.Model):
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='children', verbose_name="Parent")
    childname = models.CharField(max_length=255, verbose_name="Child Name")
    dob = models.DateField(verbose_name="Date of Birth")
    gender = models.CharField(max_length=50, verbose_name="Gender")
    blood_group = models.CharField(max_length=10, blank=True, null=True, verbose_name="Blood Group")
    
    @property
    def age(self):
        import datetime
        today = datetime.date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def __str__(self):
        return self.childname


class VaccineCardUpload(models.Model):
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='card_uploads', verbose_name="Patient")
    image = models.ImageField(upload_to="vaccine_cards/", verbose_name="Vaccine Card Image")
    extracted_data = models.JSONField(null=True, blank=True, verbose_name="Extracted Data")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At")

    def __str__(self):
        return f"Upload by {self.patient.name} at {self.created_at}"


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


class RFIDCard(models.Model):
    """Persistent RFID Card mapping to Patient/Family (NOT per-child).
    One RFID device represents the entire family and can access
    vaccination records of all children belonging to that user."""
    card_number = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="RFID Card Number")
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='rfid_cards', verbose_name="Patient Account")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    assigned_by_hospital = models.ForeignKey(
        Hospitaltbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='assigned_rfid_cards', verbose_name="Assigned By Hospital"
    )
    assigned_by_staff = models.CharField(max_length=255, blank=True, default='', verbose_name="Assigned By Staff")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RFID {self.card_number} → {self.patient.name}"


class VaccinationTransaction(models.Model):
    """Tracks the lifecycle of a single vaccination visit from RFID scan #1 to scan #2.
    Created at first RFID scan (check-in), completed at second RFID scan (vaccination done)."""
    STATUS_CHOICES = [
        ('CHECKED_IN', 'Checked In'),
        ('VERIFIED', 'Verified'),
        ('IN_PROGRESS', 'Vaccination In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    appointment = models.OneToOneField(Appointmenttbl, on_delete=models.CASCADE, related_name='transaction')
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='vaccination_transactions')
    child = models.ForeignKey(Childtbl, on_delete=models.CASCADE, related_name='vaccination_transactions')
    rfid_card = models.ForeignKey(RFIDCard, on_delete=models.CASCADE, related_name='vaccination_transactions')
    hospital = models.ForeignKey(Hospitaltbl, on_delete=models.CASCADE, related_name='vaccination_transactions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CHECKED_IN')
    scan1_time = models.DateTimeField(auto_now_add=True, verbose_name="First RFID Scan Time")
    scan2_time = models.DateTimeField(null=True, blank=True, verbose_name="Second RFID Scan Time")
    scan1_receptionist = models.ForeignKey(
        Receptionisttbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='scan1_transactions', verbose_name="Check-in Receptionist"
    )
    scan2_receptionist = models.ForeignKey(
        Receptionisttbl, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='scan2_transactions', verbose_name="Completion Receptionist"
    )
    notes = models.TextField(blank=True, default='', verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction #{self.pk} — {self.child.childname} ({self.status})"


class RFIDAssignmentLog(models.Model):
    """Audit trail for RFID card assignments and reassignments."""
    ACTION_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('DEACTIVATED', 'Deactivated'),
        ('REASSIGNED', 'Reassigned'),
    ]
    rfid_card = models.ForeignKey(RFIDCard, on_delete=models.CASCADE, related_name='assignment_logs')
    patient = models.ForeignKey(Patienttbl, on_delete=models.CASCADE, related_name='rfid_assignment_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.CharField(max_length=255, verbose_name="Performed By")
    hospital = models.ForeignKey(Hospitaltbl, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action}: RFID {self.rfid_card.card_number} → {self.patient.name}"