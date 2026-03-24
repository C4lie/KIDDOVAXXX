"""
vaccine_recommender.py
Rule-based Smart Vaccine Recommendation Engine for KiddoVax.

How it works:
  1. Look up the child's age.
  2. Collect the canonical vaccine names due for that age band.
  3. Cross-reference with what the child has already been booked/completed for.
  4. Return Vaccinetbl rows from the selected hospital whose names match the
     remaining due vaccines (case-insensitive keyword match).
"""

from django.apps import apps  # type: ignore[import]  # pyre-ignore
from .models import Childtbl, Appointmenttbl  # type: ignore[import]  # pyre-ignore

# ---------------------------------------------------------------------------
# Vaccine Schedule
# Each entry: (min_age_years, max_age_years_exclusive, [canonical keywords])
# Keywords are matched case-insensitively against Vaccinetbl.vaccineName.
# ---------------------------------------------------------------------------
VACCINE_SCHEDULE = [
    (0,  1,  ["bcg", "hepatitis b", "hep b", "opv", "ipv", "dtap", "pcv", "rotavirus", "hib"]),
    (1,  2,  ["measles", "mmr", "varicella", "chickenpox", "hepatitis a", "hep a", "influenza", "flu"]),
    (2,  5,  ["dtap", "dtp", "mmr", "varicella", "chickenpox", "polio", "ipv", "opv", "pcv", "hib"]),
    (5,  12, ["tdap", "td", "influenza", "flu", "meningococcal", "hpv"]),
    (12, 19, ["hpv", "tdap", "td", "influenza", "flu", "meningococcal"]),
    (0,  18, ["covid", "covid-19"]),   # universal for all children
]


def _get_due_keywords(age_years: int) -> set:
    """Return the set of lowercase vaccine keywords due for the given age."""
    due = set()
    for min_age, max_age, keywords in VACCINE_SCHEDULE:
        if min_age <= age_years < max_age:
            due.update(kw.lower() for kw in keywords)
    return due


def _name_matches_any(vaccine_name: str, keywords: set) -> bool:
    """Return True if any keyword appears inside the vaccine name string."""
    name_lower = vaccine_name.lower()
    return any(kw in name_lower for kw in keywords)


def get_recommended_vaccines(child_id: int, hospital_id: int):
    """
    Returns a Vaccinetbl queryset of recommended vaccines for the child.

    Logic:
      - Determine due vaccines by age.
      - Remove vaccines the child already has an active booking or completion for.
      - Filter remaining by what is actually offered at the specified hospital.

    Returns an empty list on any error so the booking flow is never broken.
    """
    try:
        child = Childtbl.objects.get(pk=child_id)
        age = child.age  # uses the @property from models.py

        due_keywords = _get_due_keywords(age)
        if not due_keywords:
            return []

        # Vaccines already booked or completed by this child (any status)
        already_booked_ids = set(
            Appointmenttbl.objects.filter(child_id=child_id)
            .values_list('vaccineid_id', flat=True)
        )

        # All vaccines offered at this hospital
        Vaccinetbl = apps.get_model('hospitalapp', 'Vaccinetbl')
        hospital_vaccines = Vaccinetbl.objects.filter(hospitalId=hospital_id)

        # Final filter: name matches a due keyword AND not already booked
        recommendations = [
            v for v in hospital_vaccines
            if _name_matches_any(v.vaccineName, due_keywords)
            and v.pk not in already_booked_ids
        ]

        return recommendations

    except Exception:
        # Never crash the booking flow
        return []


# ---------------------------------------------------------------------------
# Missed Vaccine Detection
# ---------------------------------------------------------------------------

def _get_all_due_keywords_by_age(age_years: int) -> list:
    """
    Return a list of (keywords_set, label) for every age band whose
    window has fully CLOSED before the child's current age.

    Example: A child aged 4 has fully passed the 0-1 and 1-2 windows,
    so ALL those vaccines are "should have been done" by now.
    """
    past_bands = []
    for min_age, max_age, keywords in VACCINE_SCHEDULE:
        # Band is missed if its upper bound is <= current age
        # (i.e., the window has fully elapsed)
        if max_age <= age_years:
            label = f"{min_age}–{max_age} yr"
            past_bands.append((set(kw.lower() for kw in keywords), label))
    return past_bands


def get_missed_vaccines(child_id: int) -> dict:
    """
    Detect vaccines the child should have received but hasn't.

    Returns a dict:
    {
        "missed": [
            {
                "name": "BCG",
                "due_age_range": "0–1 yr",
                "overdue_since": "Age 1 yr (now X yr old)",
                "severity": "high"   # low / medium / high
            },
            ...
        ],
        "total_missed": N,
        "overall_severity": "medium"
    }
    Returns empty result on any error.
    """
    empty = {"missed": [], "total_missed": 0, "overall_severity": "low"}
    try:
        child = Childtbl.objects.get(pk=child_id)
        age = child.age  # int, years

        past_bands = _get_all_due_keywords_by_age(age)
        if not past_bands:
            return empty  # child is too young to have missed anything yet

        # IDs of vaccines already received / booked by this child
        received_ids = set(
            Appointmenttbl.objects.filter(child_id=child_id)
            .values_list('vaccineid_id', flat=True)
        )

        # All vaccine names the child has received (for keyword matching)
        Vaccinetbl = apps.get_model('hospitalapp', 'Vaccinetbl')
        received_names = set(
            v.vaccineName.lower()
            for v in Vaccinetbl.objects.filter(pk__in=received_ids)
        ) if received_ids else set()

        missed = []
        for keywords, label in past_bands:
            for kw in sorted(keywords):  # deterministic order
                # Check if any received vaccine name contains this keyword
                already_got = any(kw in rname for rname in received_names)
                if not already_got:
                    missed.append({
                        "name": kw.title(),           # e.g. "Bcg" → titlified display
                        "due_age_range": label,
                        "overdue_since": f"Should have been given at {label} (child is now {age} yr old)",
                    })

        # Assign per-item severity and compute overall
        total = len(missed)
        for item in missed:
            if total >= 5:
                item["severity"] = "high"
            elif total >= 3:
                item["severity"] = "medium"
            else:
                item["severity"] = "low"

        if total >= 5:
            overall = "high"
        elif total >= 3:
            overall = "medium"
        elif total >= 1:
            overall = "low"
        else:
            overall = "none"

        return {
            "missed": missed,
            "total_missed": total,
            "overall_severity": overall,
        }

    except Exception:
        return empty
