"""Hospital Registration Service — Manages RFID assignment and patient hospital registration."""
from patientapp.models import Patienttbl, RFIDCard, RFIDAssignmentLog
from hospitalapp.models import Hospitaltbl
from receptionistapp.services.rfid_service import generate_unique_rfid_number


def find_pending_patients(search_query=None):
    """Returns patients with PENDING_HOSPITAL_REGISTRATION status, optionally filtered by search."""
    qs = Patienttbl.objects.filter(account_status='PENDING_HOSPITAL_REGISTRATION').order_by('-id')
    if search_query:
        search_query = search_query.strip()
        qs = qs.filter(
            __import__('django.db.models', fromlist=['Q']).Q(name__icontains=search_query) |
            __import__('django.db.models', fromlist=['Q']).Q(contactNo__icontains=search_query)
        )
    return qs


def verify_patient_registration_by_phone(patient_id, phone_number, staff_name=''):
    """Hospital receptionist confirms a pending/assigned patient by their registered contact number.

    This is the final activation gate described in the requested workflow:
    1. A patient is created and left pending in the database.
    2. The receptionist selects that patient from the pending list.
    3. The receptionist generates and assigns an RFID code to the selected user.
    4. The receptionist verifies the contact phone number to confirm the patient portal.
    """
    patient = Patienttbl.objects.filter(pk=patient_id).first()
    if not patient:
        return {'success': False, 'message': 'Patient not found.'}

    phone_number = str(phone_number or '').strip()
    if not phone_number or not phone_number.isdigit():
        return {'success': False, 'message': 'A valid phone number is required.'}

    if patient.contactNo is None:
        return {'success': False, 'message': 'This patient does not yet have a registered contact number.'}

    if str(patient.contactNo) != phone_number:
        return {
            'success': False,
            'message': 'Phone number does not match the selected patient profile.',
        }

    if patient.account_status not in ('RFID_ASSIGNED', 'ACTIVE'):
        return {
            'success': False,
            'message': 'This patient is not ready for hospital confirmation. Assign an RFID first.',
        }

    if patient.account_status == 'ACTIVE':
        return {
            'success': True,
            'message': f'{patient.name} is already confirmed and can access the patient portal.',
            'patient_name': patient.name,
            'patient_id': patient.id,
            'confirmed_phone': phone_number,
        }

    patient.account_status = 'ACTIVE'
    patient.save(update_fields=['account_status'])

    return {
        'success': True,
        'message': f'{patient.name} has been verified with phone number {phone_number}, and the patient portal is now active.',
        'patient_name': patient.name,
        'patient_id': patient.id,
        'confirmed_phone': phone_number,
    }


def register_patient_at_hospital(patient_id, hospital_id, rfid_card_number, staff_name=''):
    """
    Called when hospital staff registers a patient and assigns RFID.
    1. Validates RFID uniqueness
    2. Creates RFIDCard linked to patient (not child)
    3. Updates patient.account_status to RFID_ASSIGNED
    4. Creates RFIDAssignmentLog entry
    Returns dict with success status and message.
    """
    rfid_card_number = str(rfid_card_number).strip()
    if not rfid_card_number or not rfid_card_number.isdigit():
        return {'success': False, 'message': 'Invalid RFID card format. Must be numeric.'}

    patient = Patienttbl.objects.filter(pk=patient_id).first()
    if not patient:
        return {'success': False, 'message': 'Patient not found.'}

    hospital = Hospitaltbl.objects.filter(pk=hospital_id).first()
    if not hospital:
        return {'success': False, 'message': 'Hospital not found.'}

    # Check RFID uniqueness
    existing_rfid = RFIDCard.objects.filter(card_number=rfid_card_number).first()
    if existing_rfid:
        if existing_rfid.patient_id == patient_id and existing_rfid.is_active:
            return {'success': False, 'message': f'RFID {rfid_card_number} is already assigned to this patient.'}
        elif existing_rfid.is_active:
            return {
                'success': False,
                'message': f'RFID {rfid_card_number} is already assigned to another patient ({existing_rfid.patient.name}).'
            }

    # Deactivate any existing active RFID for this patient
    RFIDCard.objects.filter(patient_id=patient_id, is_active=True).update(is_active=False)

    # Create or reactivate RFID card
    rfid_card, created = RFIDCard.objects.get_or_create(
        card_number=rfid_card_number,
        defaults={
            'patient': patient,
            'is_active': True,
            'assigned_by_hospital': hospital,
            'assigned_by_staff': staff_name,
        }
    )

    if not created:
        # Reactivate previously deactivated card
        rfid_card.patient = patient
        rfid_card.is_active = True
        rfid_card.assigned_by_hospital = hospital
        rfid_card.assigned_by_staff = staff_name
        rfid_card.save()

    # Update patient status
    patient.account_status = 'RFID_ASSIGNED'
    patient.registered_hospital = hospital
    patient.save(update_fields=['account_status', 'registered_hospital'])

    # Create audit log
    RFIDAssignmentLog.objects.create(
        rfid_card=rfid_card,
        patient=patient,
        action='ASSIGNED',
        performed_by=staff_name,
        hospital=hospital,
    )

    return {
        'success': True,
        'message': f'RFID {rfid_card_number} successfully assigned to {patient.name}. Patient status updated to RFID_ASSIGNED.',
        'card_number': rfid_card_number,
        'patient_name': patient.name,
        'patient_id': patient.id,
    }


def reassign_rfid(old_rfid_number, new_patient_id, staff_name, hospital_id):
    """Deactivates old RFID association and assigns to new patient with audit trail."""
    old_rfid = RFIDCard.objects.filter(card_number=str(old_rfid_number).strip(), is_active=True).first()
    if not old_rfid:
        return {'success': False, 'message': 'Active RFID card not found.'}

    old_patient = old_rfid.patient
    hospital = Hospitaltbl.objects.filter(pk=hospital_id).first()

    # Deactivate old assignment
    old_rfid.is_active = False
    old_rfid.save(update_fields=['is_active'])

    RFIDAssignmentLog.objects.create(
        rfid_card=old_rfid,
        patient=old_patient,
        action='DEACTIVATED',
        performed_by=staff_name,
        hospital=hospital,
    )

    # Assign to new patient
    new_patient = Patienttbl.objects.filter(pk=new_patient_id).first()
    if not new_patient:
        return {'success': False, 'message': 'New patient not found.'}

    new_rfid = RFIDCard.objects.create(
        card_number=old_rfid.card_number,
        patient=new_patient,
        is_active=True,
        assigned_by_hospital=hospital,
        assigned_by_staff=staff_name,
    )

    RFIDAssignmentLog.objects.create(
        rfid_card=new_rfid,
        patient=new_patient,
        action='REASSIGNED',
        performed_by=staff_name,
        hospital=hospital,
    )

    return {
        'success': True,
        'message': f'RFID {old_rfid.card_number} reassigned from {old_patient.name} to {new_patient.name}.',
    }


def get_hospital_rfid_cards(hospital_id, search_query=None):
    """Returns all RFID cards assigned at a specific hospital."""
    qs = RFIDCard.objects.filter(assigned_by_hospital_id=hospital_id).select_related('patient').order_by('-created_at')
    if search_query:
        search_query = search_query.strip()
        from django.db.models import Q
        qs = qs.filter(
            Q(card_number__icontains=search_query) |
            Q(patient__name__icontains=search_query)
        )
    return qs


def get_rfid_assignment_logs(hospital_id=None, limit=50):
    """Returns RFID assignment audit logs, optionally filtered by hospital."""
    qs = RFIDAssignmentLog.objects.select_related('rfid_card', 'patient', 'hospital').order_by('-created_at')
    if hospital_id:
        qs = qs.filter(hospital_id=hospital_id)
    return qs[:limit]
