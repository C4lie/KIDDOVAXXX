import datetime
from patientapp.models import Appointmenttbl, Childtbl
from hospitalapp.models import Vaccinetbl, VaccinationRecordAlert
from patientapp.vaccine_recommender import get_missed_vaccines, get_recommended_vaccines


def calculate_appointment_priority(appointment) -> dict:
    """
    Calculates operational priority score (0 to 120) for an appointment.
    Returns:
    {
        'appointment_id': apt.id,
        'score': score,
        'priority': 'HIGH' | 'MEDIUM' | 'NORMAL' | 'LOW',
        'reasons': ['Reason 1', 'Reason 2', ...]
    }
    """
    score = 0
    reasons = []

    child = appointment.child
    hospital = appointment.hospitalid
    vaccine = appointment.vaccineid
    today = datetime.date.today()

    # 1. Overdue vaccine (+30)
    if child:
        missed = get_missed_vaccines(child.id)
        if missed.get('total_missed', 0) > 0:
            # Check if this specific vaccine is in missed list
            v_name_lower = vaccine.vaccineName.lower()
            is_this_overdue = any(m['name'].lower() in v_name_lower for m in missed.get('missed', []))
            if is_this_overdue or missed['total_missed'] >= 3:
                score += 30
                reasons.append("Vaccine appears overdue based on child's age schedule")

    # 2. Incomplete vaccination history (+25)
    if child:
        records_count = child.vaccination_records.count()
        if child.age >= 1 and records_count == 0:
            score += 25
            reasons.append("Child has incomplete recorded vaccination history")

    # 3. Required vaccine low or unavailable in hospital (+20)
    if vaccine:
        if vaccine.stock_quantity < vaccine.minimum_quantity or vaccine.stock_quantity <= 0:
            score += 20
            reasons.append(f"Hospital stock for {vaccine.vaccineName} is low ({vaccine.stock_quantity} doses left)")

    # 4. Appointment unconfirmed (+15)
    if not appointment.is_confirmed:
        score += 15
        reasons.append("Appointment confirmation has not been received from parent")

    # 5. Previous appointment missed (+10)
    if child or appointment.patientid:
        filter_kwargs = {'child': child} if child else {'patientid': appointment.patientid}
        past_unattended = Appointmenttbl.objects.filter(
            **filter_kwargs,
            aptdate__lt=today,
            active=0 # 0 = booked but never checked in/out
        ).exists()
        if past_unattended:
            score += 10
            reasons.append("Patient has a history of previously un-attended appointments")

    # 6. Multiple vaccines due at the same time (+10)
    if child and hospital:
        recs = get_recommended_vaccines(child.id, hospital.id)
        if len(recs) > 1:
            score += 10
            reasons.append(f"Multiple ({len(recs)}) vaccine doses are due for this child")

    # 7. Record quality warning (+10)
    if child:
        has_alerts = VaccinationRecordAlert.objects.filter(
            child=child,
            status='PENDING'
        ).exists()
        if has_alerts:
            score += 10
            reasons.append("Vaccination record quality verification alert requires staff attention")

    # Priority mapping
    if score >= 70:
        priority = 'HIGH'
    elif score >= 40:
        priority = 'MEDIUM'
    elif score >= 20:
        priority = 'NORMAL'
    else:
        priority = 'LOW'

    if not reasons:
        reasons.append("Routine vaccination appointment")

    return {
        'appointment_id': appointment.id,
        'appointment': appointment,
        'score': score,
        'priority': priority,
        'reasons': reasons
    }


def get_prioritized_queue_for_hospital(hospital_id: int, date_val: datetime.date = None) -> list:
    """
    Returns today's appointment queue for a hospital, sorted by:
    1. Priority level (HIGH -> MEDIUM -> NORMAL -> LOW)
    2. Appointment time ascending
    """
    if date_val is None:
        date_val = datetime.date.today()

    appointments = Appointmenttbl.objects.filter(
        hospitalid_id=hospital_id,
        aptdate=date_val
    ).exclude(active__in=[2, 3]).select_related('child', 'vaccineid', 'patientid', 'hospitalid')

    priority_map = {'HIGH': 0, 'MEDIUM': 1, 'NORMAL': 2, 'LOW': 3}
    evaluated_queue = []

    for apt in appointments:
        res = calculate_appointment_priority(apt)
        evaluated_queue.append(res)

    # Sort queue
    def sort_key(item):
        p_val = priority_map.get(item['priority'], 9)
        time_val = item['appointment'].apttime or datetime.time(23, 59, 59)
        return (p_val, time_val, item['appointment_id'])

    evaluated_queue.sort(key=sort_key)
    return evaluated_queue
