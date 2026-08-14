import datetime
from patientapp.models import Childtbl, Appointmenttbl, VaccinationRecord
from hospitalapp.models import VaccinationRecordAlert


def run_quality_check_for_child(child_id: int) -> list:
    """
    Scans all completed appointments and vaccination records for a child,
    identifies quality anomalies, and persists alerts into VaccinationRecordAlert.
    Returns the list of created or updated alerts.
    """
    try:
        child = Childtbl.objects.get(pk=child_id)
    except Childtbl.DoesNotExist:
        return []

    alerts = []
    child_dob = child.dob

    # Fetch all completed appointments/records
    appointments = Appointmenttbl.objects.filter(
        child=child,
        active=2 # Completed
    ).select_related('vaccineid', 'hospitalid').order_by('aptdate')

    recorded_vaccines = VaccinationRecord.objects.filter(
        child=child
    ).select_related('vaccine', 'appointment').order_by('created_at')

    # 1. IMPOSSIBLE DATE CHECK: Vaccination before birth
    for apt in appointments:
        if apt.aptdate and apt.aptdate < child_dob:
            alert, _ = VaccinationRecordAlert.objects.get_or_create(
                child=child,
                appointment=apt,
                issue_type='IMPOSSIBLE_DATE',
                vaccine_name=apt.vaccineid.vaccineName,
                defaults={
                    'severity': 'HIGH',
                    'description': f"Vaccination date ({apt.aptdate.strftime('%d/%m/%Y')}) appears to be before child DOB ({child_dob.strftime('%d/%m/%Y')}).",
                    'recommended_action': "Verify original paper vaccination record and correct the date."
                }
            )
            alerts.append(alert)

    # 2. DUPLICATE RECORD CHECK: Same vaccine administered on same date or multiple times
    vaccine_date_map = {}
    for apt in appointments:
        v_name = apt.vaccineid.vaccineName
        key = (v_name.lower(), apt.aptdate)
        if key in vaccine_date_map:
            prev_apt = vaccine_date_map[key]
            alert, _ = VaccinationRecordAlert.objects.get_or_create(
                child=child,
                appointment=apt,
                issue_type='DUPLICATE_RECORD',
                vaccine_name=v_name,
                defaults={
                    'severity': 'MEDIUM',
                    'description': f"Possible duplicate {v_name} record detected on {apt.aptdate.strftime('%d/%m/%Y')}.",
                    'recommended_action': "Review vaccination document to confirm if duplicate entry exists."
                }
            )
            alerts.append(alert)
        else:
            vaccine_date_map[key] = apt

    # 3. SUSPICIOUS DOSE INTERVAL CHECK
    # Check multi-dose series like DTaP, Hep B, OPV
    series_groups = {}
    for apt in appointments:
        v_name = apt.vaccineid.vaccineName
        # Group by series key e.g. "dtap", "hepatitis-b", "opv", "rotavirus"
        base_name = v_name.split()[0].replace('-', '').lower()
        if base_name not in series_groups:
            series_groups[base_name] = []
        if apt.aptdate:
            series_groups[base_name].append((apt.aptdate, apt))

    for base_name, entries in series_groups.items():
        entries.sort(key=lambda x: x[0])
        for i in range(1, len(entries)):
            prev_date, prev_apt = entries[i-1]
            curr_date, curr_apt = entries[i]
            gap_days = (curr_date - prev_date).days
            
            # Minimum recommended interval is 28 days
            if gap_days < 28:
                alert, _ = VaccinationRecordAlert.objects.get_or_create(
                    child=child,
                    appointment=curr_apt,
                    issue_type='SUSPICIOUS_INTERVAL',
                    vaccine_name=curr_apt.vaccineid.vaccineName,
                    defaults={
                        'severity': 'MEDIUM',
                        'description': f"Short interval detected: {curr_apt.vaccineid.vaccineName} given only {gap_days} days after previous dose ({prev_date.strftime('%d/%m/%Y')}). Recommended minimum is 28 days.",
                        'recommended_action': "Verify dose administration dates on the child's record before proceeding."
                    }
                )
                alerts.append(alert)

    # 4. MISSING INTERMEDIATE DOSE CHECK
    # E.g. Child has Dose 3 or Booster but no Dose 1 or 2
    given_names_lower = [apt.vaccineid.vaccineName.lower() for apt in appointments if apt.vaccineid]
    for name in given_names_lower:
        if '3' in name or 'booster' in name:
            base_prefix = name.split()[0]
            has_dose1 = any(base_prefix in n and ('1' in n or 'birth' in n or n == base_prefix) for n in given_names_lower)
            if not has_dose1:
                alert, _ = VaccinationRecordAlert.objects.get_or_create(
                    child=child,
                    issue_type='MISSING_DOSE',
                    vaccine_name=name.title(),
                    defaults={
                        'severity': 'MEDIUM',
                        'description': f"Later dose '{name.title()}' recorded, but earlier initial dose was not found in record history.",
                        'recommended_action': "Check whether initial dose was administered elsewhere and update history."
                    }
                )
                alerts.append(alert)

    return alerts
