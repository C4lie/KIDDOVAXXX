"""
RFID Service — Core business logic for the RFID-based vaccination workflow.

This service handles:
1. Family-based RFID scanning (one RFID → one user/family → multiple children)
2. Dual-mode scan detection (check-in vs completion)
3. Full verification chain (user, child, appointment, hospital, vaccine, date, time)
4. Check-in with VaccinationTransaction creation
5. Vaccination completion with record creation
6. Queue position assignment

Both the RFID Simulator and future physical RFID readers call these same functions.
"""
import random
import datetime
from django.utils import timezone
from patientapp.models import (
    RFIDCard, Patienttbl, Childtbl, Appointmenttbl,
    VaccinationTransaction, VaccinationRecord,
)
from hospitalapp.models import Vaccinetbl, Receptionisttbl, VaccinationRecordAlert


def generate_unique_rfid_number() -> str:
    """Generates an 8-digit unique RFID card string e.g., '10384721'."""
    while True:
        num = str(random.randint(10000000, 99999999))
        if not RFIDCard.objects.filter(card_number=num).exists():
            return num


def scan_rfid_card(card_number: str, hospital_id: int = None) -> dict:
    """
    Core RFID Scan Service — Two-mode operation:

    MODE 1 (First Scan — Check-in):
        RFID → Patient/Family → All Children → Today's appointments at THIS hospital
        Returns list of children with their appointments, prioritized by appointment time.
        Children with appointments appear FIRST.

    MODE 2 (Second Scan — Completion):
        RFID → Find active VaccinationTransaction at THIS hospital
        Returns the in-progress transaction details for completion.

    The mode is automatically determined:
    - If an active VaccinationTransaction exists at this hospital → MODE 2
    - Otherwise → MODE 1
    """
    card_number = str(card_number).strip()
    if not card_number or not card_number.isdigit() or len(card_number) < 4:
        return {
            'found': False,
            'status': 'INVALID_INPUT',
            'error': 'Invalid RFID card format. Must be numeric.',
        }

    # Find the RFID card
    rfid_obj = RFIDCard.objects.filter(
        card_number=card_number, is_active=True
    ).select_related('patient').first()

    if not rfid_obj:
        return {
            'found': False,
            'status': 'NOT_REGISTERED',
            'card_number': card_number,
            'message': 'No patient is associated with this RFID card.',
        }

    patient = rfid_obj.patient
    today = datetime.date.today()

    # ─── MODE 2: Check for active vaccination transaction ───
    active_txn = VaccinationTransaction.objects.filter(
        rfid_card=rfid_obj,
        status__in=['CHECKED_IN', 'VERIFIED', 'IN_PROGRESS'],
    ).select_related(
        'appointment', 'child', 'hospital', 'appointment__vaccineid',
    ).first()

    if hospital_id and active_txn:
        # Only match transactions at this specific hospital
        if active_txn.hospital_id != hospital_id:
            active_txn = None

    if active_txn:
        return {
            'found': True,
            'mode': 'COMPLETION',
            'card_number': card_number,
            'patient': _serialize_patient(patient),
            'active_transaction': {
                'id': active_txn.id,
                'appointment_id': active_txn.appointment_id,
                'child': _serialize_child(active_txn.child),
                'vaccine_name': active_txn.appointment.vaccineid.vaccineName if active_txn.appointment.vaccineid else '',
                'hospital_name': active_txn.hospital.title if active_txn.hospital else '',
                'status': active_txn.status,
                'scan1_time': active_txn.scan1_time.strftime('%I:%M %p') if active_txn.scan1_time else '',
                'apt_time': active_txn.appointment.apttime.strftime('%I:%M %p') if active_txn.appointment.apttime else 'Anytime',
                'apt_date': active_txn.appointment.aptdate.strftime('%Y-%m-%d') if active_txn.appointment.aptdate else '',
            },
        }

    # ─── MODE 1: Check-in — Find family + children + today's appointments ───
    children = list(Childtbl.objects.filter(patient=patient).order_by('dob'))

    # Get today's appointments for ALL children of this patient at this hospital
    apt_qs = Appointmenttbl.objects.filter(
        patientid=patient,
        aptdate=today,
        active__in=[Appointmenttbl.STATUS_BOOKED, Appointmenttbl.STATUS_CHECKED_IN],
    ).select_related('vaccineid', 'hospitalid', 'child')

    if hospital_id:
        apt_qs = apt_qs.filter(hospitalid_id=hospital_id)

    today_appointments = list(apt_qs.order_by('apttime', 'id'))

    # Build children list with their appointments, children with appointments FIRST
    children_with_apts = []
    children_without_apts = []

    for child in children:
        child_apts = [a for a in today_appointments if a.child_id == child.id]
        child_data = _serialize_child(child)
        child_data['appointments'] = [_serialize_appointment(a) for a in child_apts]
        child_data['has_appointment_today'] = len(child_apts) > 0

        if child_apts:
            children_with_apts.append(child_data)
        else:
            children_without_apts.append(child_data)

    # Also handle appointments without child FK (legacy data)
    orphan_apts = [a for a in today_appointments if a.child_id is None]

    return {
        'found': True,
        'mode': 'CHECKIN',
        'card_number': card_number,
        'child': _serialize_child(children[0]) if children else None,
        'patient': _serialize_patient(patient),
        'children': children_with_apts + children_without_apts,
        'orphan_appointments': [_serialize_appointment(a) for a in orphan_apts],
        'total_appointments_today': len(today_appointments),
    }


def verify_appointment(appointment_id: int, rfid_number: str, hospital_id: int = None) -> dict:
    """
    Full verification chain for an appointment before check-in:
    1. User verification — RFID belongs to this user
    2. Child verification — child belongs to this user
    3. Appointment verification — appointment exists
    4. Hospital verification — appointment is at THIS hospital
    5. Vaccine verification — vaccine is scheduled and in stock
    6. Date verification — appointment is today
    7. Time verification — early / on-time / late
    """
    apt = Appointmenttbl.objects.filter(id=appointment_id).select_related(
        'patientid', 'child', 'vaccineid', 'hospitalid',
    ).first()

    if not apt:
        return {'verified': False, 'status': 'APPOINTMENT_NOT_FOUND', 'checks': [], 'message': 'Appointment not found.'}

    rfid_card = RFIDCard.objects.filter(card_number=str(rfid_number).strip(), is_active=True).first()
    if not rfid_card:
        return {'verified': False, 'status': 'RFID_NOT_FOUND', 'checks': [], 'message': 'RFID card not found.'}

    checks = []
    all_passed = True
    today = datetime.date.today()

    # 1. User verification
    if rfid_card.patient_id == apt.patientid_id:
        checks.append({'name': 'User Match', 'passed': True, 'detail': f'RFID belongs to {rfid_card.patient.name}'})
    else:
        checks.append({'name': 'User Match', 'passed': False, 'detail': 'RFID does not belong to this patient account.'})
        all_passed = False

    # 2. Child verification
    if apt.child and apt.child.patient_id == rfid_card.patient_id:
        checks.append({'name': 'Child Match', 'passed': True, 'detail': f'{apt.child.childname} belongs to this family'})
    elif apt.child:
        checks.append({'name': 'Child Match', 'passed': False, 'detail': 'Child does not belong to this RFID holder.'})
        all_passed = False
    else:
        checks.append({'name': 'Child Match', 'passed': True, 'detail': 'Legacy appointment (no child profile linked)'})

    # 3. Appointment exists and is bookable
    if apt.active == Appointmenttbl.STATUS_BOOKED:
        checks.append({'name': 'Appointment Status', 'passed': True, 'detail': 'Appointment is confirmed and ready'})
    elif apt.active == Appointmenttbl.STATUS_CHECKED_IN:
        checks.append({'name': 'Appointment Status', 'passed': True, 'detail': 'Already checked in'})
    else:
        checks.append({'name': 'Appointment Status', 'passed': False, 'detail': f'Appointment status is {apt.status_label}'})
        all_passed = False

    # 4. Hospital verification
    if hospital_id and apt.hospitalid_id != hospital_id:
        checks.append({
            'name': 'Hospital Match', 'passed': False,
            'detail': f'Appointment is at {apt.hospitalid.title}, not at this hospital.'
        })
        all_passed = False
    else:
        checks.append({'name': 'Hospital Match', 'passed': True, 'detail': f'Appointment is at {apt.hospitalid.title}'})

    # 5. Vaccine verification
    if apt.vaccineid:
        stock = apt.vaccineid.stock_quantity
        if stock > 0:
            checks.append({'name': 'Vaccine Available', 'passed': True, 'detail': f'{apt.vaccineid.vaccineName} in stock ({stock} doses)'})
        else:
            checks.append({'name': 'Vaccine Available', 'passed': False, 'detail': f'{apt.vaccineid.vaccineName} is OUT OF STOCK'})
            all_passed = False
    else:
        checks.append({'name': 'Vaccine Available', 'passed': False, 'detail': 'No vaccine assigned'})
        all_passed = False

    # 6. Date verification
    if apt.aptdate == today:
        checks.append({'name': 'Date Match', 'passed': True, 'detail': 'Appointment is scheduled for today'})
    else:
        checks.append({'name': 'Date Match', 'passed': False, 'detail': f'Appointment is for {apt.aptdate}, not today'})
        all_passed = False

    # 7. Time verification
    timing_status = 'ON_TIME'
    delay_minutes = 0
    if apt.apttime:
        now_time = datetime.datetime.now()
        scheduled_dt = datetime.datetime.combine(today, apt.apttime)
        diff_seconds = (now_time - scheduled_dt).total_seconds()
        diff_mins = int(diff_seconds / 60)

        if diff_mins > 15:
            timing_status = 'LATE'
            delay_minutes = diff_mins
            checks.append({'name': 'Timing', 'passed': True, 'detail': f'Late by {diff_mins} minutes'})
        elif diff_mins < -30:
            timing_status = 'EARLY'
            checks.append({'name': 'Timing', 'passed': True, 'detail': 'Arriving earlier than scheduled'})
        else:
            checks.append({'name': 'Timing', 'passed': True, 'detail': 'On time'})
    else:
        checks.append({'name': 'Timing', 'passed': True, 'detail': 'No specific time scheduled'})

    # 8. Quality alerts check
    quality_alerts_count = 0
    if apt.child:
        quality_alerts_count = VaccinationRecordAlert.objects.filter(
            child=apt.child, status='PENDING'
        ).count()
        if quality_alerts_count > 0:
            checks.append({
                'name': 'Record Quality', 'passed': False,
                'detail': f'{quality_alerts_count} pending quality alert(s) for this child'
            })
        else:
            checks.append({'name': 'Record Quality', 'passed': True, 'detail': 'No pending alerts'})

    overall_status = 'READY_FOR_CHECKIN' if all_passed else 'REQUIRES_STAFF_REVIEW'

    return {
        'verified': all_passed,
        'status': overall_status,
        'checks': checks,
        'timing_status': timing_status,
        'delay_minutes': delay_minutes,
        'quality_alerts_count': quality_alerts_count,
        'appointment': _serialize_appointment(apt),
        'patient_name': apt.patientid.name if apt.patientid else '',
        'child_name': apt.child.childname if apt.child else apt.childname or '',
    }


def checkin_patient(appointment_id: int, rfid_number: str, receptionist_id: int = None, hospital_id: int = None) -> dict:
    """
    Performs check-in after verification:
    1. Creates VaccinationTransaction
    2. Updates appointment status to CHECKED_IN
    3. Assigns queue position
    4. Records check-in time and RFID used
    """
    apt = Appointmenttbl.objects.filter(id=appointment_id).select_related(
        'patientid', 'child', 'vaccineid', 'hospitalid',
    ).first()

    if not apt:
        return {'success': False, 'message': 'Appointment not found.'}

    if apt.active not in (Appointmenttbl.STATUS_BOOKED,):
        return {'success': False, 'message': f'Appointment is not in BOOKED status. Current: {apt.status_label}'}

    rfid_card = RFIDCard.objects.filter(card_number=str(rfid_number).strip(), is_active=True).first()
    if not rfid_card:
        return {'success': False, 'message': 'RFID card not found or inactive.'}

    # Verify RFID belongs to this patient
    if rfid_card.patient_id != apt.patientid_id:
        return {'success': False, 'message': 'RFID card does not belong to this patient.'}

    now = datetime.datetime.now()

    # Calculate queue position
    today = datetime.date.today()
    h_id = hospital_id or apt.hospitalid_id
    current_queue_count = VaccinationTransaction.objects.filter(
        hospital_id=h_id,
        scan1_time__date=today,
        status__in=['CHECKED_IN', 'VERIFIED', 'IN_PROGRESS'],
    ).count()
    queue_pos = current_queue_count + 1

    # Create vaccination transaction
    txn = VaccinationTransaction.objects.create(
        appointment=apt,
        patient=apt.patientid,
        child=apt.child,
        rfid_card=rfid_card,
        hospital_id=h_id,
        status='CHECKED_IN',
        scan1_receptionist_id=receptionist_id,
    )

    # Update appointment
    apt.active = Appointmenttbl.STATUS_CHECKED_IN
    apt.checkin_rfid = rfid_number
    apt.checkin_time = now
    apt.checkin_receptionist_id = receptionist_id
    apt.queue_position = queue_pos
    apt.rfidno = int(rfid_number) if rfid_number.isdigit() else None
    apt.indt = now
    apt.save(update_fields=[
        'active', 'checkin_rfid', 'checkin_time', 'checkin_receptionist_id',
        'queue_position', 'rfidno', 'indt',
    ])

    return {
        'success': True,
        'message': f'Patient checked in successfully. Queue position: #{queue_pos}',
        'transaction_id': txn.id,
        'appointment_id': apt.id,
        'queue_position': queue_pos,
        'child_name': apt.child.childname if apt.child else apt.childname or '',
        'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else '',
    }


def complete_vaccination(transaction_id: int, rfid_number: str, receptionist_id: int = None) -> dict:
    """
    Second RFID scan handler — completes the vaccination:
    1. Verifies same RFID as check-in
    2. Verifies same child
    3. Marks transaction COMPLETED
    4. Updates appointment to COMPLETED (active=4)
    5. Creates/updates VaccinationRecord
    6. Decrements vaccine stock
    7. Runs quality check
    """
    txn = VaccinationTransaction.objects.filter(id=transaction_id).select_related(
        'appointment', 'child', 'rfid_card', 'hospital',
        'appointment__vaccineid', 'appointment__patientid',
    ).first()

    if not txn:
        return {'success': False, 'message': 'Vaccination transaction not found.'}

    if txn.status not in ('CHECKED_IN', 'VERIFIED', 'IN_PROGRESS'):
        return {'success': False, 'message': f'Transaction is not active. Current status: {txn.status}'}

    # Verify RFID match
    if txn.rfid_card.card_number != str(rfid_number).strip():
        return {
            'success': False,
            'message': 'RFID mismatch! The scanned RFID does not match the check-in RFID. '
                       f'Expected: {txn.rfid_card.card_number}, Got: {rfid_number}',
        }

    now = datetime.datetime.now()
    apt = txn.appointment

    # Mark transaction completed
    txn.status = 'COMPLETED'
    txn.scan2_time = now
    txn.scan2_receptionist_id = receptionist_id
    txn.save(update_fields=['status', 'scan2_time', 'scan2_receptionist_id', 'updated_at'])

    # Update appointment
    apt.active = Appointmenttbl.STATUS_COMPLETED
    apt.completion_rfid = rfid_number
    apt.completion_time = now
    apt.completion_receptionist_id = receptionist_id
    apt.outdt = now
    apt.save(update_fields=['active', 'completion_rfid', 'completion_time', 'completion_receptionist_id', 'outdt'])

    # Decrement vaccine stock
    if apt.vaccineid and apt.vaccineid.stock_quantity > 0:
        apt.vaccineid.stock_quantity = max(0, apt.vaccineid.stock_quantity - 1)
        apt.vaccineid.save(update_fields=['stock_quantity'])

    # Auto-create VaccinationRecord
    record_created = False
    if txn.child:
        _, record_created = VaccinationRecord.objects.get_or_create(
            appointment=apt,
            defaults={
                'child': txn.child,
                'vaccine': apt.vaccineid,
            }
        )

        # Run quality check
        try:
            from patientapp.services.quality_checker_service import run_quality_check_for_child
            run_quality_check_for_child(txn.child_id)
        except Exception:
            pass

    return {
        'success': True,
        'message': f'Vaccination completed for {txn.child.childname if txn.child else "patient"}.',
        'transaction_id': txn.id,
        'appointment_id': apt.id,
        'child_name': txn.child.childname if txn.child else '',
        'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else '',
        'record_created': record_created,
        'completed_at': now.strftime('%I:%M %p'),
    }


def link_rfid_card(card_number: str, patient_id: int, child_id: int = None) -> dict:
    """Permanently links an RFID card number to a Patient profile (family-level, not child)."""
    card_number = str(card_number).strip()
    if not card_number or not card_number.isdigit():
        return {'success': False, 'message': 'Invalid RFID card format.'}

    patient = Patienttbl.objects.filter(pk=patient_id).first()
    if not patient:
        return {'success': False, 'message': 'Patient not found.'}

    rfid_obj, created = RFIDCard.objects.get_or_create(
        card_number=card_number,
        defaults={
            'patient': patient,
            'is_active': True,
        }
    )

    if not created:
        if rfid_obj.patient_id != patient_id:
            return {
                'success': False,
                'message': f'RFID card {card_number} is already assigned to another patient ({rfid_obj.patient.name}).',
            }
        rfid_obj.is_active = True
        rfid_obj.save(update_fields=['is_active'])

    return {
        'success': True,
        'message': f'RFID card {card_number} successfully linked to {patient.name}.',
        'card_number': card_number,
        'patient_name': patient.name,
    }


# ─── Internal serializers ───

def _serialize_patient(patient):
    """Serialize patient for API responses."""
    return {
        'id': patient.id,
        'name': patient.name,
        'contact': str(patient.contactNo) if patient.contactNo else '',
        'address': patient.address,
        'account_status': patient.account_status,
    }


def _serialize_child(child):
    """Serialize child for API responses."""
    return {
        'id': child.id,
        'name': child.childname,
        'dob': child.dob.strftime('%Y-%m-%d') if child.dob else '',
        'age': child.age,
        'gender': child.gender,
    }


def _serialize_appointment(apt):
    """Serialize appointment for API responses."""
    return {
        'id': apt.id,
        'child_name': apt.child.childname if apt.child else apt.childname or '',
        'child_id': apt.child_id,
        'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else '',
        'hospital_name': apt.hospitalid.title if apt.hospitalid else '',
        'hospital_id': apt.hospitalid_id,
        'apt_date': apt.aptdate.strftime('%Y-%m-%d') if apt.aptdate else '',
        'apt_time': apt.apttime.strftime('%I:%M %p') if apt.apttime else 'Anytime',
        'status': apt.status_label,
        'active': apt.active,
        'is_confirmed': apt.is_confirmed,
    }
