"""
vaccine_recommender.py
Rule-based Smart Vaccine Recommendation Engine for KiddoVax.

Calculates all compulsory UIP vaccines due for a child from birth up to current age (days/weeks/months/years).
"""
import datetime
from django.apps import apps
from .models import Childtbl, Appointmenttbl
from hospitalapp.models import Vaccinetbl

# ---------------------------------------------------------------------------
# Universal Immunization Programme (UIP) Milestone Schedule
# (min_age_days, milestone_label, [compulsory_vaccine_names])
# ---------------------------------------------------------------------------
UIP_MILESTONES = [
    (0, "At Birth", [
        "BCG",
        "Hepatitis B (Birth Dose)",
        "OPV-0"
    ]),
    (42, "6 Weeks", [
        "OPV-1",
        "Pentavalent-1",
        "Rotavirus-1",
        "fIPV-1",
        "PCV-1"
    ]),
    (70, "10 Weeks", [
        "OPV-2",
        "Pentavalent-2",
        "Rotavirus-2"
    ]),
    (98, "14 Weeks", [
        "OPV-3",
        "Pentavalent-3",
        "Rotavirus-3",
        "fIPV-2",
        "PCV-2"
    ]),
    (270, "9–12 Months", [
        "MR-1",
        "PCV Booster",
        "fIPV-3",
        "JE-1",
        "Vitamin A (1st Dose)"
    ]),
    (480, "16–24 Months", [
        "MR-2",
        "DPT Booster-1",
        "OPV Booster",
        "JE-2",
        "Vitamin A (Bi-annual)"
    ]),
    (1825, "5–6 Years", [
        "DPT Booster-2"
    ]),
    (3650, "10 Years", [
        "Td (10 Years)"
    ]),
    (5840, "16 Years", [
        "Td (16 Years)"
    ]),
]


def get_due_uip_vaccines_for_child(child):
    """
    Returns list of dicts:
    [{'name': 'BCG', 'milestone': 'At Birth', 'min_days': 0}, ...]
    for all compulsory vaccines due from birth up to child's current age in days.
    """
    today = datetime.date.today()
    if not child.dob:
        return []
    
    age_days = (today - child.dob).days
    if age_days < 0:
        age_days = 0

    due_vaccines = []
    seen_names = set()

    for min_days, milestone_name, vaccine_list in UIP_MILESTONES:
        if age_days >= min_days:
            for v_name in vaccine_list:
                if v_name.lower() not in seen_names:
                    seen_names.add(v_name.lower())
                    due_vaccines.append({
                        'name': v_name,
                        'milestone': milestone_name,
                        'min_days': min_days
                    })
                    
    return due_vaccines


def get_recommended_vaccines(child_id: int, hospital_id: int = None):
    """
    Returns Vaccinetbl objects of compulsory due vaccines
    that the child has NOT yet received or booked.
    """
    try:
        child = Childtbl.objects.get(pk=child_id)
        due_uip = get_due_uip_vaccines_for_child(child)
        if not due_uip:
            return []

        # Vaccines already booked/completed by this child (excluding CANCELLED=5)
        booked_apts = Appointmenttbl.objects.filter(child_id=child_id).exclude(active=Appointmenttbl.STATUS_CANCELLED)
        already_booked_vaccine_ids = set(booked_apts.values_list('vaccineid_id', flat=True))
        already_booked_names = set(
            a.vaccineid.vaccineName.lower() for a in booked_apts if a.vaccineid
        )

        # Get hospital inventory
        if hospital_id:
            hosp_vaccines = list(Vaccinetbl.objects.filter(hospitalId_id=hospital_id))
        else:
            hosp_vaccines = list(Vaccinetbl.objects.all())

        if hospital_id and not hosp_vaccines:
            hosp_vaccines = list(Vaccinetbl.objects.all())

        recommendations = []
        seen_rec_names = set()

        for due_item in due_uip:
            d_name = due_item['name']
            d_lower = d_name.lower()

            # Skip if child already booked/received this vaccine
            if any(d_lower == r_name or d_lower in r_name or r_name in d_lower for r_name in already_booked_names):
                continue

            if d_lower in seen_rec_names:
                continue

            # Find matching vaccine in hospital inventory
            matched_v = None
            for v in hosp_vaccines:
                v_lower = v.vaccineName.lower()
                if (d_lower == v_lower or d_lower in v_lower or v_lower in d_lower) and v.pk not in already_booked_vaccine_ids:
                    matched_v = v
                    break
            
            if matched_v and matched_v not in recommendations:
                matched_v.due_stage = due_item['milestone']
                matched_v.schedule_desc = f"Compulsory dose due ({due_item['milestone']})"
                recommendations.append(matched_v)
                seen_rec_names.add(d_lower)
            elif not matched_v:
                # Construct fallback item so compulsory UIP vaccine is always shown
                fb_v = Vaccinetbl(
                    pk=0,
                    vaccineName=d_name,
                    vaccineDescr=f"Compulsory dose due ({due_item['milestone']})",
                    price=0
                )
                fb_v.due_stage = due_item['milestone']
                fb_v.schedule_desc = f"Compulsory dose due ({due_item['milestone']})"
                recommendations.append(fb_v)
                seen_rec_names.add(d_lower)

        return recommendations
    except Exception as e:
        return []


def get_missed_vaccines(child_id: int) -> dict:
    """
    Detects vaccines due for previous milestones that have passed overdue window.
    """
    empty = {"missed": [], "total_missed": 0, "overall_severity": "none"}
    try:
        child = Childtbl.objects.get(pk=child_id)
        if not child.dob:
            return empty

        today = datetime.date.today()
        age_days = (today - child.dob).days

        # Vaccines already booked/completed
        booked_apts = Appointmenttbl.objects.filter(child_id=child_id).exclude(active=Appointmenttbl.STATUS_CANCELLED)
        already_booked_names = set(
            a.vaccineid.vaccineName.lower() for a in booked_apts if a.vaccineid
        )

        missed = []
        for min_days, milestone_name, vaccine_list in UIP_MILESTONES:
            # Overdue if milestone passed by more than 14 days
            if age_days >= (min_days + 14):
                for v_name in vaccine_list:
                    v_lower = v_name.lower()
                    if not any(v_lower == r_name or v_lower in r_name or r_name in v_lower for r_name in already_booked_names):
                        tomorrow_str = (today + datetime.timedelta(days=1)).strftime('%d %B, %Y')
                        missed.append({
                            "name": v_name,
                            "due_age_range": milestone_name,
                            "overdue_since": f"Overdue from {milestone_name} milestone",
                            "catch_up_date": f"Recommended Date: {tomorrow_str}"
                        })

        total = len(missed)
        for item in missed:
            if total >= 5:
                item["severity"] = "high"
            elif total >= 3:
                item["severity"] = "medium"
            else:
                item["severity"] = "low"

        overall = "high" if total >= 5 else ("medium" if total >= 3 else ("low" if total >= 1 else "none"))
        return {
            "missed": missed,
            "total_missed": total,
            "overall_severity": overall,
        }
    except Exception:
        return empty
