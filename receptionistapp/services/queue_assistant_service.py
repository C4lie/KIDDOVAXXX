"""
Queue Assistant Service — Digital queue powered by VaccinationTransaction.

Uses the new transaction model for accurate real-time queue state:
- WAITING: Has transaction with status CHECKED_IN / VERIFIED
- IN_PROGRESS: Has transaction with status IN_PROGRESS
- COMPLETED: Has transaction with status COMPLETED
- NOT_ARRIVED: Has appointment but no transaction yet
"""
import datetime
from django.utils import timezone
from patientapp.models import Appointmenttbl, Childtbl, VaccinationTransaction
from hospitalapp.models import Vaccinetbl, VaccinationRecordAlert


def get_receptionist_counter_queue(hospital_id: int) -> dict:
    """
    Analyzes today's counter queue state for receptionists.
    Uses VaccinationTransaction for accurate status tracking.
    """
    today = datetime.date.today()
    now_dt = datetime.datetime.now()

    # Get all today's appointments at this hospital
    appointments = Appointmenttbl.objects.filter(
        hospitalid_id=hospital_id,
        aptdate=today
    ).select_related('patientid', 'child', 'vaccineid').order_by('apttime', 'id')

    total_count = appointments.count()
    waiting_list = []
    in_progress_list = []
    not_arrived_list = []
    completed_list = []
    late_count = 0
    no_show_count = 0

    # Get active transactions for this hospital today
    transactions = VaccinationTransaction.objects.filter(
        hospital_id=hospital_id,
        scan1_time__date=today,
    ).select_related('appointment', 'child', 'patient', 'appointment__vaccineid')

    txn_by_apt = {txn.appointment_id: txn for txn in transactions}

    for apt in appointments:
        apt_time_str = apt.apttime.strftime('%I:%M %p') if apt.apttime else 'Anytime'
        txn = txn_by_apt.get(apt.id)

        if txn:
            if txn.status in ('CHECKED_IN', 'VERIFIED'):
                # WAITING
                wait_mins = 0
                if txn.scan1_time:
                    scan1_naive = txn.scan1_time.replace(tzinfo=None) if txn.scan1_time.tzinfo else txn.scan1_time
                    wait_mins = max(0, int((now_dt - scan1_naive).total_seconds() / 60))

                waiting_list.append({
                    'id': apt.id,
                    'transaction_id': txn.id,
                    'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                    'child_name': apt.child.childname if apt.child else apt.childname or '',
                    'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                    'apt_time': apt_time_str,
                    'checkin_time': txn.scan1_time.strftime('%I:%M %p') if txn.scan1_time else '',
                    'waiting_minutes': wait_mins,
                    'is_long_wait': wait_mins >= 20,
                    'queue_position': apt.queue_position or 0,
                    'rfidno': apt.rfidno,
                    'status': txn.status,
                })

            elif txn.status == 'IN_PROGRESS':
                # IN PROGRESS
                wait_mins = 0
                if txn.scan1_time:
                    scan1_naive = txn.scan1_time.replace(tzinfo=None) if txn.scan1_time.tzinfo else txn.scan1_time
                    wait_mins = max(0, int((now_dt - scan1_naive).total_seconds() / 60))

                in_progress_list.append({
                    'id': apt.id,
                    'transaction_id': txn.id,
                    'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                    'child_name': apt.child.childname if apt.child else apt.childname or '',
                    'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                    'apt_time': apt_time_str,
                    'checkin_time': txn.scan1_time.strftime('%I:%M %p') if txn.scan1_time else '',
                    'duration_minutes': wait_mins,
                    'status': txn.status,
                })

            elif txn.status == 'COMPLETED':
                # COMPLETED
                completed_list.append({
                    'id': apt.id,
                    'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                    'child_name': apt.child.childname if apt.child else apt.childname or '',
                    'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                    'apt_time': apt_time_str,
                    'completed_at': txn.scan2_time.strftime('%I:%M %p') if txn.scan2_time else '',
                    'status': txn.status,
                })

        elif apt.active in (Appointmenttbl.STATUS_VERIFIED, Appointmenttbl.STATUS_COMPLETED):
            # Completed / Verified without transaction
            completed_list.append({
                'id': apt.id,
                'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                'child_name': apt.child.childname if (apt.child and hasattr(apt.child, 'childname')) else apt.childname or '',
                'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                'apt_time': apt_time_str,
                'completed_at': apt.outdt.strftime('%I:%M %p') if apt.outdt else '',
                'status': 'COMPLETED',
            })

        elif apt.active == Appointmenttbl.STATUS_VACCINATION_IN_PROGRESS:
            in_progress_list.append({
                'id': apt.id,
                'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                'child_name': apt.child.childname if (apt.child and hasattr(apt.child, 'childname')) else apt.childname or '',
                'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                'apt_time': apt_time_str,
                'checkin_time': apt.indt.strftime('%I:%M %p') if apt.indt else '',
                'duration_minutes': 0,
                'status': 'IN_PROGRESS',
            })

        elif apt.active == Appointmenttbl.STATUS_CHECKED_IN:
            waiting_list.append({
                'id': apt.id,
                'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                'child_name': apt.child.childname if (apt.child and hasattr(apt.child, 'childname')) else apt.childname or '',
                'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                'apt_time': apt_time_str,
                'checkin_time': apt.indt.strftime('%I:%M %p') if apt.indt else '',
                'waiting_minutes': 0,
                'is_long_wait': False,
                'queue_position': apt.queue_position or 0,
                'rfidno': apt.rfidno,
                'status': 'CHECKED_IN',
            })

        elif apt.active == Appointmenttbl.STATUS_CANCELLED:
            pass  # Skip cancelled

        else:
            # NOT ARRIVED — scheduled but no transaction yet
            is_late = False
            delay_mins = 0
            if apt.apttime:
                sched_dt = datetime.datetime.combine(today, apt.apttime)
                if now_dt > sched_dt + datetime.timedelta(minutes=15):
                    is_late = True
                    delay_mins = int((now_dt - sched_dt).total_seconds() / 60)
                    late_count += 1
                if now_dt > sched_dt + datetime.timedelta(minutes=60):
                    no_show_count += 1

            not_arrived_list.append({
                'id': apt.id,
                'patient_name': apt.patientid.name if apt.patientid else apt.childname or '',
                'child_name': apt.child.childname if (apt.child and hasattr(apt.child, 'childname')) else apt.childname or '',
                'vaccine_name': apt.vaccineid.vaccineName if apt.vaccineid else 'General',
                'apt_time': apt_time_str,
                'is_late': is_late,
                'delay_minutes': delay_mins,
                'is_confirmed': apt.is_confirmed,
            })

    # AI Operational Queue Insights
    ai_insights = []

    long_waiters = [p for p in waiting_list if p.get('waiting_minutes', 0) >= 20]
    if long_waiters:
        names = ", ".join([p['child_name'] or p['patient_name'] for p in long_waiters[:2]])
        ai_insights.append(f"⚠️ {len(long_waiters)} patient(s) waiting over 20 mins ({names}). Recommend expediting.")

    if late_count > 0:
        ai_insights.append(f"⏰ {late_count} scheduled appointment(s) running late. Consider outreach or slot reuse.")

    if no_show_count > 0:
        ai_insights.append(f"💡 {no_show_count} appointment(s) likely no-show (60+ min past scheduled). Slots available for walk-ins.")

    if in_progress_list:
        ai_insights.append(f"💉 {len(in_progress_list)} vaccination(s) currently in progress.")

    if not waiting_list and not_arrived_list:
        ai_insights.append("✓ Waiting room clear. Next scheduled patient expected shortly.")
    elif not appointments:
        ai_insights.append("✓ No appointments booked for today. System ready for walk-in registrations.")
    else:
        total_done = len(completed_list)
        total_remaining = len(waiting_list) + len(not_arrived_list) + len(in_progress_list)
        if total_done > 0:
            ai_insights.append(f"📊 Progress: {total_done} completed, {total_remaining} remaining today.")

    return {
        'total_count': total_count,
        'total_appointments': total_count,
        'checked_in_count': len(waiting_list) + len(in_progress_list) + len(completed_list),
        'waiting_count': len(waiting_list),
        'in_progress_count': len(in_progress_list),
        'not_arrived_count': len(not_arrived_list),
        'completed_count': len(completed_list),
        'late_count': late_count,
        'no_show_count': no_show_count,
        'waiting_list': waiting_list,
        'in_progress_list': in_progress_list,
        'not_arrived_list': not_arrived_list,
        'completed_list': completed_list,
        'ai_insights': ai_insights,
    }
