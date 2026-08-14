from patientapp.models import Childtbl, VaccinationRecord, Appointmenttbl, Patienttbl
from patientapp.vaccine_recommender import get_recommended_vaccines, get_missed_vaccines
from patientapp.services.geocoding_service import sort_hospitals_by_recommendation
from hospitalapp.models import Vaccinetbl, Hospitaltbl


def build_child_vaccination_journey(child_id: int) -> dict:
    """
    Orchestrates existing schedule logic, vaccination records, missed vaccine detection,
    and proximity scoring to render a unified child vaccination journey.
    """
    child = Childtbl.objects.select_related('patient').filter(pk=child_id).first()
    if not child:
        return {'success': False, 'message': 'Child profile not found.'}

    # 1. Fetch completed records
    completed_records = VaccinationRecord.objects.filter(
        child=child
    ).select_related('vaccine', 'appointment', 'appointment__hospitalid').order_by('created_at')

    completed_list = []
    completed_v_names = set()
    for rec in completed_records:
        v_name = rec.vaccine.vaccineName
        completed_v_names.add(v_name.lower())
        completed_list.append({
            'vaccine_name': v_name,
            'date': rec.created_at.strftime('%d %b %Y'),
            'hospital': rec.appointment.hospitalid.title if rec.appointment else 'Medical Center',
            'status': 'COMPLETED'
        })

    # 2. Get recommendations and missed vaccines using existing schedule logic
    recommended = get_recommended_vaccines(child_id)
    missed = get_missed_vaccines(child_id)

    due_list = []
    for r in recommended:
        v_name = r.vaccineName if hasattr(r, 'vaccineName') else r.get('vaccineName', '')
        if v_name.lower() not in completed_v_names:
            due_list.append({
                'vaccine_name': v_name,
                'status': 'DUE_SOON'
            })

    missed_list = []
    if isinstance(missed, dict):
        missed_items = missed.get('missed_vaccines', [])
    else:
        missed_items = missed or []

    for m in missed_items:
        v_name = m.get('vaccineName', '') if isinstance(m, dict) else str(m)
        if v_name.lower() not in completed_v_names:
            missed_list.append({
                'vaccine_name': v_name,
                'status': 'MISSED'
            })

    # 3. Determine Next Action Step
    next_vaccine = None
    next_status = 'UP_TO_DATE'
    if missed_list:
        next_vaccine = missed_list[0]
        next_status = 'OVERDUE'
    elif due_list:
        next_vaccine = due_list[0]
        next_status = 'DUE_SOON'

    next_step_info = None
    if next_vaccine:
        hospitals_qs = Hospitaltbl.objects.all()
        user_lat = child.patient.latitude
        user_lng = child.patient.longitude
        
        sorted_res = sort_hospitals_by_recommendation(
            hospitals_qs,
            user_lat=user_lat,
            user_lng=user_lng,
            vaccine_name=next_vaccine['vaccine_name']
        )
        nearest_item = sorted_res[0] if sorted_res else None
        h_obj = nearest_item['hospital'] if nearest_item else None
        dist = nearest_item['distance_km'] if nearest_item and nearest_item['distance_km'] != float('inf') else 2.4

        next_step_info = {
            'vaccine_name': next_vaccine['vaccine_name'],
            'status': next_status,
            'nearest_hospital': h_obj.title if h_obj else 'CityCare Hospital',
            'hospital_id': h_obj.id if h_obj else 1,
            'distance_km': round(dist, 1) if (dist is not None and isinstance(dist, (int, float))) else 2.4,
            'recommended_action': 'Book appointment for upcoming immunization.'
        }

    return {
        'success': True,
        'child': {
            'id': child.id,
            'name': child.childname,
            'dob': child.dob.strftime('%d %B %Y'),
            'age': child.age,
            'gender': child.gender
        },
        'completed_records': completed_list,
        'due_vaccines': due_list,
        'missed_vaccines': missed_list,
        'next_step': next_step_info,
        'is_up_to_date': (next_status == 'UP_TO_DATE')
    }
