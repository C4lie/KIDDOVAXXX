"""
notification_service.py
Service layer for managing patient notifications in KiddoVax.

Handles:
- Dynamic real-time calculation of appointment notifications:
  * Upcoming appointments (imminent/near-booking vs future)
  * Delayed / missed appointments & overdue vaccines
  * Completed appointments & immunization milestones
- AI-Powered Contextual Insights & Pediatric Guidance for each notification
- Read/Unread tracking with DB persistence and session synchronization
"""

import datetime
from typing import Dict, Any, List, Optional
from django.utils import timezone

from patientapp.models import (
    Appointmenttbl,
    Childtbl,
    Notification,
    VaccinationRecord,
    Patienttbl,
)
from hospitalapp.models import Vaccinetbl
from patientapp.vaccine_recommender import get_missed_vaccines


# ---------------------------------------------------------------------------
# AI Clinical & Preparation Insights Generator
# ---------------------------------------------------------------------------

def generate_ai_insight(
    category: str,
    vaccine_name: str,
    child_name: str,
    days_diff: Optional[int] = None,
    time_str: Optional[str] = None,
) -> str:
    """
    Generates intelligent pediatric guidance and tips tailored to the appointment context.
    """
    v_clean = (vaccine_name or '').lower()

    if category == 'imminent':  # Today or Tomorrow
        if 'bcg' in v_clean:
            return "AI Preparation: BCG is given intradermally. A small red bump is normal after 2-3 weeks. Keep the area clean and dry."
        elif 'polio' in v_clean or 'opv' in v_clean or 'ipv' in v_clean:
            return "AI Preparation: Oral drops or fractional dose. Baby can be breastfed/fed immediately after. Arrive 10m early for quick RFID verification."
        elif 'penta' in v_clean or 'dpt' in v_clean:
            return "AI Preparation: 5-in-1 vaccine protects against Diphtheria, Pertussis, Tetanus, HepB, and Hib. Mild soreness or fussiness is common post-dose."
        elif 'rotavirus' in v_clean:
            return "AI Preparation: Oral vaccine protecting against severe viral diarrhea. Ensure baby is calm and unhurried during administration."
        elif 'mmr' in v_clean or 'mr' in v_clean:
            return "AI Preparation: Measles/Rubella immunization. Mild low-grade fever may occur 7-10 days later as antibodies build."
        else:
            time_note = f" at {time_str}" if time_str else ""
            return f"AI Tip: Your appointment is approaching{time_note}. Bring the child's immunization card and arrive 10 min early for seamless check-in."

    elif category == 'upcoming':
        if days_diff is not None and days_diff <= 3:
            return f"AI Reminder: Scheduled in {days_diff} days. Ensure {child_name} is in good health with no high fever on appointment day."
        return f"AI Note: Keep this scheduled milestone in your calendar. Prompt vaccination ensures uninterrupted pediatric immunity."

    elif category == 'delayed':
        return (
            f"AI Clinical Advisory: Delaying {vaccine_name or 'routine doses'} increases susceptibility to preventable infections. "
            "Catch-up immunization is safe and does not require restarting earlier doses. Please reschedule soon."
        )

    elif category == 'completed':
        if 'penta' in v_clean or 'dpt' in v_clean:
            return "AI Aftercare: Apply a cool, damp cloth to reduce injection site soreness. Give plenty of fluids and monitor temperature."
        elif 'bcg' in v_clean:
            return "AI Aftercare: Do not apply oils, ointments, or bandages to the BCG site. A natural small crust will form and heal."
        else:
            return "AI Milestone: Vaccination successfully completed! Child's digital immunity passport has been updated."

    return "AI Insight: Verified and tracked via KiddoVax Smart Healthcare Network."


# ---------------------------------------------------------------------------
# Notification Service Core Functions
# ---------------------------------------------------------------------------

def get_patient_notifications(patient_id: int, last_read_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Synthesizes all appointment-related notifications and system alerts for a patient.
    Categories:
      - 'upcoming' / 'imminent'
      - 'delayed'
      - 'completed'
      - 'general'
    """
    if not patient_id:
        return {'notifications': [], 'unread_count': 0, 'stats': {'upcoming': 0, 'delayed': 0, 'completed': 0, 'total': 0}}

    today = datetime.date.today()
    notifications_list: List[Dict[str, Any]] = []

    # 1. Fetch Patient Appointments
    appointments = Appointmenttbl.objects.filter(patientid=patient_id).select_related(
        'child', 'vaccineid', 'hospitalid'
    ).order_by('aptdate', 'apttime')

    # 2. Process Appointments
    for apt in appointments:
        child_name = apt.display_child_name
        vaccine_name = apt.vaccineid.vaccineName if apt.vaccineid else "Vaccine"
        hospital_name = apt.hospitalid.title if apt.hospitalid else "Clinic"
        apt_date = apt.aptdate
        apt_time = apt.apttime

        date_str = apt_date.strftime('%b %d, %Y') if apt_date else "Not Scheduled"
        time_str = apt_time.strftime('%I:%M %p') if apt_time else ""

        # Determine relative status
        if apt.active == Appointmenttbl.STATUS_COMPLETED or apt.active == Appointmenttbl.STATUS_VERIFIED:
            # COMPLETED APPOINTMENT
            completed_dt = apt.completion_time or apt.outdt or (datetime.datetime.combine(apt_date, datetime.time.min) if apt_date else timezone.now())
            is_read = (last_read_time is not None)

            ai_note = generate_ai_insight('completed', vaccine_name, child_name)

            notifications_list.append({
                'id': f"apt-completed-{apt.id}",
                'appointment_id': apt.id,
                'category': 'completed',
                'title': f"Vaccination Completed — {child_name}",
                'message': f"{child_name} successfully received {vaccine_name} at {hospital_name}.",
                'child_name': child_name,
                'vaccine_name': vaccine_name,
                'hospital_name': hospital_name,
                'date_str': date_str,
                'time_str': time_str,
                'badge_label': 'COMPLETED',
                'badge_color': 'green',
                'icon': 'check_circle',
                'ai_insight': ai_note,
                'is_read': is_read,
                'action_url': '/patient/journey/',
                'action_label': 'View Journey',
                'timestamp': completed_dt.isoformat() if hasattr(completed_dt, 'isoformat') else str(completed_dt),
                'urgency': 'low',
            })

        elif apt.active in [Appointmenttbl.STATUS_BOOKED, Appointmenttbl.STATUS_CHECKED_IN]:
            if apt_date is not None and apt_date < today:
                # DELAYED / MISSED APPOINTMENT
                is_read = (last_read_time is not None)
                ai_note = generate_ai_insight('delayed', vaccine_name, child_name)
                days_overdue = (today - apt_date).days

                notifications_list.append({
                    'id': f"apt-delayed-{apt.id}",
                    'appointment_id': apt.id,
                    'category': 'delayed',
                    'title': f"Delayed Appointment — {child_name}",
                    'message': f"Appointment for {vaccine_name} at {hospital_name} was scheduled for {date_str} ({days_overdue} days ago) and was missed.",
                    'child_name': child_name,
                    'vaccine_name': vaccine_name,
                    'hospital_name': hospital_name,
                    'date_str': date_str,
                    'time_str': time_str,
                    'badge_label': f'OVERDUE {days_overdue}D',
                    'badge_color': 'red',
                    'icon': 'warning',
                    'ai_insight': ai_note,
                    'is_read': is_read,
                    'action_url': '/patient/vaccinebooking/',
                    'action_label': 'Reschedule Now',
                    'timestamp': datetime.datetime.combine(apt_date, apt_time or datetime.time.min).isoformat(),
                    'urgency': 'high',
                })

            elif apt_date is not None:
                # UPCOMING APPOINTMENT
                days_diff = (apt_date - today).days

                if days_diff == 0:
                    badge_label = 'TODAY'
                    badge_color = 'amber'
                    urgency = 'high'
                    imminent_cat = 'imminent'
                    rel_phrase = f"Today at {time_str}" if time_str else "Today"
                elif days_diff == 1:
                    badge_label = 'TOMORROW'
                    badge_color = 'cyan'
                    urgency = 'high'
                    imminent_cat = 'imminent'
                    rel_phrase = f"Tomorrow at {time_str}" if time_str else "Tomorrow"
                elif days_diff <= 3:
                    badge_label = f'IN {days_diff} DAYS'
                    badge_color = 'blue'
                    urgency = 'medium'
                    imminent_cat = 'imminent'
                    rel_phrase = f"in {days_diff} days ({date_str}{' at ' + time_str if time_str else ''})"
                else:
                    badge_label = 'UPCOMING'
                    badge_color = 'indigo'
                    urgency = 'low'
                    imminent_cat = 'upcoming'
                    rel_phrase = f"on {date_str}{' at ' + time_str if time_str else ''}"

                ai_note = generate_ai_insight(imminent_cat, vaccine_name, child_name, days_diff=days_diff, time_str=time_str)

                # Unread until acknowledged / marked read
                is_read = (last_read_time is not None)

                notifications_list.append({
                    'id': f"apt-upcoming-{apt.id}",
                    'appointment_id': apt.id,
                    'category': 'upcoming',
                    'title': f"Upcoming Appointment — {child_name}",
                    'message': f"{vaccine_name} at {hospital_name} is scheduled for {rel_phrase}.",
                    'child_name': child_name,
                    'vaccine_name': vaccine_name,
                    'hospital_name': hospital_name,
                    'date_str': date_str,
                    'time_str': time_str,
                    'badge_label': badge_label,
                    'badge_color': badge_color,
                    'icon': 'event_upcoming' if days_diff > 1 else 'alarm_on',
                    'ai_insight': ai_note,
                    'is_read': is_read,
                    'action_url': '/patient/vaccinebooking/',
                    'action_label': 'View / Manage',
                    'timestamp': datetime.datetime.combine(apt_date, apt_time or datetime.time.min).isoformat(),
                    'urgency': urgency,
                })

    # 3. Check Overdue Vaccines for Children without active appointments
    try:
        children = Childtbl.objects.filter(patient_id=patient_id)
        for child in children:
            missed_res = get_missed_vaccines(child.id)
            if missed_res.get('total_missed', 0) > 0:
                # Check if there is already an upcoming appointment booked for any missed vaccine
                missed_names = [v.get('vaccine_name') for v in missed_res.get('missed_vaccines', []) if v.get('vaccine_name')]
                # Filter out ones already covered by pending appointments
                covered_vacs = Appointmenttbl.objects.filter(
                    child=child,
                    active__in=[Appointmenttbl.STATUS_BOOKED, Appointmenttbl.STATUS_CHECKED_IN]
                ).values_list('vaccineid__vaccineName', flat=True)

                uncovered_missed = [name for name in missed_names if name not in covered_vacs]

                if uncovered_missed:
                    count_uncovered = len(uncovered_missed)
                    sample_vac = uncovered_missed[0]
                    vac_text = f"{sample_vac}" if count_uncovered == 1 else f"{sample_vac} (+{count_uncovered - 1} more)"
                    ai_note = generate_ai_insight('delayed', vac_text, child.childname)

                    notifications_list.append({
                        'id': f"child-missed-{child.id}",
                        'category': 'delayed',
                        'title': f"Vaccine Milestone Due — {child.childname}",
                        'message': f"{child.childname} is due for routine immunization ({vac_text}). No active booking found.",
                        'child_name': child.childname,
                        'vaccine_name': vac_text,
                        'hospital_name': "Preferred Health Facility",
                        'date_str': "Milestone Due",
                        'time_str': "",
                        'badge_label': f"{count_uncovered} DUE",
                        'badge_color': 'amber',
                        'icon': 'medical_services',
                        'ai_insight': ai_note,
                        'is_read': (last_read_time is not None),
                        'action_url': '/patient/vaccinebooking/',
                        'action_label': 'Book Appointment',
                        'timestamp': timezone.now().isoformat(),
                        'urgency': 'high',
                    })
    except Exception:
        pass

    # 4. Include Stored Database Notifications (SMS reminders, etc.)
    db_notifs = Notification.objects.filter(patient_id=patient_id).order_by('-created_at')[:15]
    for n in db_notifs:
        # Avoid duplicate messages if already captured via live appointment
        if n.related_id and any(
            (item.get('appointment_id') == n.related_id and item.get('category') in ['upcoming', 'delayed'])
            for item in notifications_list
        ):
            continue

        notifications_list.append({
            'id': f"db-{n.id}",
            'category': 'general' if n.notification_type not in ['upcoming', 'delayed', 'completed'] else n.notification_type,
            'title': "KiddoVax Alert",
            'message': n.message,
            'child_name': "",
            'vaccine_name': "",
            'hospital_name': "",
            'date_str': n.created_at.strftime('%b %d, %Y'),
            'time_str': n.created_at.strftime('%I:%M %p'),
            'badge_label': 'ALERT',
            'badge_color': 'teal',
            'icon': 'notifications',
            'ai_insight': "AI Guidance: Automated alert recorded in your child's immunization profile.",
            'is_read': n.is_read,
            'action_url': '/patient/journey/',
            'action_label': 'Open Journey',
            'timestamp': n.created_at.isoformat(),
            'urgency': 'medium' if not n.is_read else 'low',
        })

    # Sort notifications by urgency (high > medium > low) and then latest
    urgency_order = {'high': 0, 'medium': 1, 'low': 2}
    notifications_list.sort(key=lambda x: (urgency_order.get(x.get('urgency', 'low'), 2), not x.get('is_read', False)), reverse=False)

    # Compute Stats
    upcoming_count = sum(1 for n in notifications_list if n.get('category') in ['upcoming', 'imminent'])
    delayed_count = sum(1 for n in notifications_list if n.get('category') == 'delayed')
    completed_count = sum(1 for n in notifications_list if n.get('category') == 'completed')
    unread_count = sum(1 for n in notifications_list if not n.get('is_read', False))

    return {
        'notifications': notifications_list,
        'unread_count': unread_count,
        'stats': {
            'upcoming': upcoming_count,
            'delayed': delayed_count,
            'completed': completed_count,
            'total': len(notifications_list),
        }
    }


def mark_patient_notifications_read(patient_id: int, request: Optional[Any] = None) -> bool:
    """
    Marks all notifications for this patient as read in the database
    and stores the current timestamp in user session.
    """
    if not patient_id:
        return False

    # Mark database records read
    Notification.objects.filter(patient_id=patient_id, is_read=False).update(is_read=True)

    # Store last read timestamp in session
    if request and hasattr(request, 'session'):
        request.session['last_notifications_read_at'] = timezone.now().isoformat()
        request.session.modified = True

    return True
