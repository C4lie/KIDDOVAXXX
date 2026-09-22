"""
ai_assistant_service.py
Core AI Vaccination Assistant Service for KiddoVax.

Implements:
- NLP Intent Recognition & Entity Extraction
- Verified Pediatric Vaccine Knowledge Base (with clinical safety boundaries)
- Child-Specific Immunization Schedule Analysis & Recommendations
- Conversational Multi-turn Appointment Booking State Machine
- Integration with existing Appointmenttbl, Hospitaltbl, Vaccinetbl, and booking_service
"""

import re
import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from patientapp.models import Patienttbl, Appointmenttbl, Childtbl, VaccinationRecord
from hospitalapp.models import Hospitaltbl, Vaccinetbl, HospitalHoliday, HospitalBreak
from patientapp.vaccine_recommender import UIP_MILESTONES, get_due_uip_vaccines_for_child, get_recommended_vaccines, get_missed_vaccines
from patientapp.services.booking_service import generate_hospital_time_slots, validate_and_reserve_slot


# ---------------------------------------------------------------------------
# Medical Safety Disclaimer
# ---------------------------------------------------------------------------
MEDICAL_SAFETY_DISCLAIMER = (
    "⚠️ **Medical Disclaimer**: Vaccination information provided by this assistant is for general guidance. "
    "Please consult a qualified healthcare professional or your pediatrician for official medical advice."
)


# ---------------------------------------------------------------------------
# Verified Pediatric Vaccine Knowledge Base
# ---------------------------------------------------------------------------
VACCINE_KNOWLEDGE_BASE = {
    'bcg': {
        'name': 'BCG (Bacillus Calmette-Guérin)',
        'type': 'Live attenuated bacterial vaccine',
        'prevents': 'Severe forms of Tuberculosis (TB), particularly tubercular meningitis and disseminated TB in infants.',
        'purpose': 'Provides crucial early-life defense against severe mycobacterial infections prevalent in young children.',
        'schedule': 'Administered at birth or as soon as possible during early infancy (single intradermal dose).',
        'aftercare': 'A small red papule/bump typically develops at the injection site after 2–3 weeks, eventually forming a tiny characteristic scar. This is normal and expected.'
    },
    'hepb': {
        'name': 'Hepatitis B Vaccine',
        'type': 'Recombinant protein subunit vaccine',
        'prevents': 'Hepatitis B virus (HBV) infection, which causes chronic liver disease, cirrhosis, and liver cancer.',
        'purpose': 'Prevents vertical transmission from mother to infant and horizontal childhood transmission.',
        'schedule': 'Birth dose (within 24 hours of birth) followed by primary series at 6, 10, and 14 weeks (often in Pentavalent combination).',
        'aftercare': 'Mild soreness or redness at injection site may occur. Apply a cool cloth if needed.'
    },
    'opv': {
        'name': 'OPV (Oral Polio Vaccine)',
        'type': 'Live attenuated viral oral drops',
        'prevents': 'Poliomyelitis (Polio), an infectious virus causing permanent muscle paralysis and disability.',
        'purpose': 'Induces mucosal intestinal immunity to stop transmission of wild and vaccine-derived poliovirus strains.',
        'schedule': 'Birth dose (OPV-0), followed by doses at 6, 10, and 14 weeks, plus a booster at 16–24 months.',
        'aftercare': 'Extremely safe with virtually no side effects. Feeds can be resumed immediately.'
    },
    'ipv': {
        'name': 'fIPV / IPV (Inactivated Polio Vaccine)',
        'type': 'Inactivated (killed) viral vaccine (fractional intradermal or intramuscular)',
        'prevents': 'All 3 types of Poliovirus, boosting blood humoral immunity against paralytic polio.',
        'purpose': 'Strengthens systemic immunity alongside oral polio drops for comprehensive national polio elimination.',
        'schedule': 'Doses at 6 weeks (fIPV-1), 14 weeks (fIPV-2), and 9 months (fIPV-3).',
        'aftercare': 'Mild localized tenderness or irritability. Keep baby comfortable and hydrated.'
    },
    'pentavalent': {
        'name': 'Pentavalent Vaccine (DPT + HepB + Hib)',
        'type': '5-in-1 Combination conjugate vaccine',
        'prevents': '5 life-threatening illnesses: Diphtheria, Pertussis (Whooping Cough), Tetanus, Hepatitis B, and Haemophilus influenzae type b (severe pneumonia & meningitis).',
        'purpose': 'Reduces the number of injections while providing robust multi-pathogen protection in early infancy.',
        'schedule': '3 primary doses given at 6 weeks, 10 weeks, and 14 weeks of age.',
        'aftercare': 'Mild fever, swelling, or fussiness may occur for 24–48 hours. Acetaminophen / Paracetamol as prescribed by doctor.'
    },
    'rotavirus': {
        'name': 'Rotavirus Vaccine (Rotavac / RotaTeq / Rotarix)',
        'type': 'Live attenuated oral drops',
        'prevents': 'Severe rotavirus-induced watery diarrhea, vomiting, and life-threatening dehydration in infants.',
        'purpose': 'Drastically lowers infant hospitalizations caused by severe diarrheal dehydration.',
        'schedule': 'Administered orally as 3 doses at 6 weeks, 10 weeks, and 14 weeks of age.',
        'aftercare': 'Infant can feed normally. Watch for severe stomach irritability or unusual stool.'
    },
    'pcv': {
        'name': 'PCV (Pneumococcal Conjugate Vaccine)',
        'type': 'Bacterial conjugate vaccine',
        'prevents': 'Invasive pneumococcal diseases caused by Streptococcus pneumoniae: Pneumonia, Meningitis, Bacteremia, and Middle Ear infections (Otitis media).',
        'purpose': 'Protects vulnerable infants from major bacterial causes of childhood respiratory mortality.',
        'schedule': 'Primary doses at 6 weeks (PCV-1) and 14 weeks (PCV-2), with a booster dose at 9–12 months.',
        'aftercare': 'Mild local swelling or low-grade temperature. Cool compresses help soothe the limb.'
    },
    'mmr': {
        'name': 'MR / MMR Vaccine (Measles, Mumps, Rubella)',
        'type': 'Live attenuated viral vaccine',
        'prevents': 'Measles (high fever, cough & body rash with fatal respiratory/brain complications), Mumps (painful salivary gland swelling), and Rubella (German measles).',
        'purpose': 'Ensures lifetime immunity (>97% protection after 2 doses) against highly contagious viral outbreaks.',
        'schedule': 'Dose 1 at 9–12 months (MR-1 / MMR-1), Dose 2 at 16–24 months (MR-2 / MMR-2).',
        'aftercare': 'Mild fever or faint rash can occasionally appear 7–12 days post-vaccination as the immune system builds defense.'
    },
    'je': {
        'name': 'JE Vaccine (Japanese Encephalitis)',
        'type': 'Live attenuated or inactivated viral vaccine',
        'prevents': 'Japanese Encephalitis, a mosquito-borne viral brain infection that causes acute encephalitis syndrome.',
        'purpose': 'Protects children in endemic and seasonal risk zones against neurological disability and fatality.',
        'schedule': 'Dose 1 at 9–12 months (alongside MR-1), Dose 2 at 16–24 months.',
        'aftercare': 'Localized pain or mild headache/fever. Ensure adequate fluid intake.'
    },
    'dpt': {
        'name': 'DPT / DTaP Booster Vaccine',
        'type': 'Toxoid & inactivated bacterial combination',
        'prevents': 'Diphtheria, Pertussis (Whooping Cough), and Tetanus.',
        'purpose': 'Renews and boosts waning antibody levels established during the infant primary pentavalent series.',
        'schedule': 'Booster 1 at 16–24 months, Booster 2 at 5–6 years of age.',
        'aftercare': 'Local arm/thigh soreness or mild fever. Keep the child rested.'
    },
    'td': {
        'name': 'Td (Tetanus & adult Diphtheria) Vaccine',
        'type': 'Toxoid vaccine with reduced diphtheria component',
        'prevents': 'Tetanus (lockjaw caused by wound contamination) and Diphtheria in older children and adolescents.',
        'purpose': 'Replaces old TT vaccine to maintain long-term diphtheria herd immunity into adulthood.',
        'schedule': 'Administered at 10 years and 16 years of age, and during pregnancy.',
        'aftercare': 'Muscle ache at upper arm injection site for 1–2 days.'
    },
    'varicella': {
        'name': 'Varicella Vaccine (Chickenpox)',
        'type': 'Live attenuated viral vaccine',
        'prevents': 'Chickenpox (varicella-zoster virus), itchy blister rashes, secondary skin infections, and pneumonia.',
        'purpose': 'Provides long-term immunity and reduces risk of shingles later in life.',
        'schedule': 'Dose 1 at 12–15 months, Dose 2 at 4–6 years of age.',
        'aftercare': 'Mild rash or brief fever. Avoid salicylates/aspirin.'
    },
    'hepa': {
        'name': 'Hepatitis A Vaccine',
        'type': 'Inactivated viral vaccine',
        'prevents': 'Hepatitis A viral liver infection spread via contaminated food and water.',
        'purpose': 'Protects against acute jaundice, liver inflammation, and gastrointestinal illness.',
        'schedule': '2 doses given at least 6 months apart, starting from 12 months of age.',
        'aftercare': 'Mild tenderness at injection site.'
    },
    'typhoid': {
        'name': 'Typhoid Conjugate Vaccine (TCV)',
        'type': 'Bacterial conjugate vaccine',
        'prevents': 'Typhoid enteric fever caused by Salmonella Typhi.',
        'purpose': 'Provides sustained protection against multi-drug resistant typhoid from 6 months of age.',
        'schedule': 'Single dose from 6–9 months onwards, booster at 2 years depending on clinical advice.',
        'aftercare': 'Low-grade fever or mild pain. Rest and hydration recommended.'
    }
}

# Symptom safety flags
ACUTE_SYMPTOM_PATTERNS = [
    r'\b(?:high\s+)?fever\s+(?:above|>)?\s*(?:10[0-9]|39|40)\b',
    r'\b(?:breathing\s+difficulty|shortness\s+of\s+breath|wheezing)\b',
    r'\b(?:seizure|convulsion|fit)\b',
    r'\b(?:allergic\s+reaction|anaphylaxis|swelling\s+face|swollen\s+throat)\b',
    r'\b(?:unresponsive|lethargic|unconscious)\b',
    r'\b(?:vomiting|severe\s+diarrhea|dehydrated)\b',
    r'\b(?:sick\s+right\s+now|very\s+ill|is\s+it\s+safe\s+to\s+give\s+if\s+child\s+is\s+sick)\b'
]


# ---------------------------------------------------------------------------
# NLP & Intent Recognition Engine
# ---------------------------------------------------------------------------

def detect_intent(message: str, context: dict) -> str:
    """
    Identifies the primary user intent from natural language input.
    """
    msg = message.strip().lower()

    # 1. Immediate Booking State Overrides if active flow in progress
    booking_step = context.get('booking_step')
    if booking_step and booking_step != 'COMPLETED':
        if re.search(r'\b(?:cancel|stop|abort|nevermind|exit|restart|reset)\b', msg) and not re.search(r'\b(?:confirm|proceed|yes)\b', msg):
            return 'cancel_booking'
        if booking_step == 'AWAITING_CONFIRMATION':
            if re.search(r'\b(?:confirm|yes|proceed|book|confirm appointment|ok|sure|schedule it)\b', msg):
                return 'confirm_booking'
            if re.search(r'\b(?:cancel|no|stop|change)\b', msg):
                return 'cancel_booking'

    # 2. Medical emergency / acute symptoms check
    for pat in ACUTE_SYMPTOM_PATTERNS:
        if re.search(pat, msg):
            return 'medical_symptom_safety'

    # 3. Active Step Selection Priority
    if booking_step:
        if booking_step == 'AWAITING_CHILD' and not re.search(r'\b(?:what|why|help|hi|hello)\b', msg):
            return 'select_child'
        elif booking_step == 'AWAITING_HOSPITAL' and not re.search(r'\b(?:what|why|help|hi|hello)\b', msg):
            return 'select_hospital'
        elif booking_step == 'AWAITING_VACCINE' and not re.search(r'\b(?:what\s+is|tell\s+me|why|side\s+effects)\b', msg):
            return 'select_vaccine'
        elif booking_step == 'AWAITING_DATE' and not re.search(r'\b(?:what|why|help|hi|hello)\b', msg):
            return 'select_date'
        elif booking_step == 'AWAITING_SLOT' and not re.search(r'\b(?:what|why|help|hi|hello)\b', msg):
            return 'select_slot'

    # 4. Appointment Status / View Bookings
    if re.search(r'\b(?:my\s+appointments?|check\s+(?:my\s+)?(?:booking|appointment)|appointment\s+status|upcoming\s+appointments?|view\s+appointments?)\b', msg):
        return 'appointment_status'

    # 5. Explicit Confirmation / Cancellation outside state machine
    if re.search(r'^(?:confirm|confirm\s+appointment|yes\s+confirm|proceed)$', msg):
        return 'confirm_booking'
    if re.search(r'^(?:cancel|cancel\s+booking|abort)$', msg):
        return 'cancel_booking'

    # 6. Natural Language Booking Intent
    if re.search(r'\b(?:book\s+(?:an?\s+)?appointment|book\s+(?:a\s+)?vaccin|schedule\s+(?:an?\s+)?appointment|want\s+(?:an?\s+)?appointment|book\s+slot|make\s+an?\s+appointment)\b', msg) or \
       re.search(r'\bbook\s+(?:my|the)?\s*(?:child|baby|kid|upcoming|mmr|bcg|polio|opv|hepb|pcv|pentavalent|rotavirus|dpt|td|vaccine)', msg):
        return 'book_appointment'

    # 7. Upcoming / Due Vaccines / Schedule Analysis
    if re.search(r'\b(?:what\s+vaccines?\s+(?:is|are)\s+(?:due|upcoming)|upcoming\s+vaccines?|due\s+vaccines?|vaccines?\s+(?:is|are)\s+due|vaccines?\s+upcoming|next\s+vaccine|schedule\s+for\s+child|what\s+is\s+coming\s+next|immunization\s+schedule|vaccine\s+schedule)\b', msg) or \
       re.search(r'\b(?:\d+\s*(?:month|year|week|day)s?\s*old.*(?:vaccine|due|next)|vaccine.*(?:for\s*\d+\s*(?:month|year|week)))', msg):
        return 'upcoming_vaccine'

    # 8. Vaccine Information / Education Intent
    if re.search(r'\b(?:what\s+is|tell\s+me\s+about|why\s+(?:is|do\s+we\s+give)|purpose\s+of|what\s+does.*prevent|what\s+type\s+of\s+vaccine|information\s+on|details\s+about|info\s+about|side\s+effects\s+of)\b', msg) or \
       any(v_key in msg for v_key in ['bcg', 'mmr', 'opv', 'ipv', 'polio', 'pentavalent', 'rotavirus', 'pcv', 'hepb', 'hepatitis', 'dpt', 'td', 'varicella', 'typhoid']):
        # If user explicitly asked "book MMR" that is caught in booking step, otherwise vaccine info
        if not re.search(r'\b(?:book|schedule)\b', msg):
            return 'vaccine_information'

    # 9. Greetings & Help
    if re.search(r'\b(?:hi|hello|hey|greetings|help|how\s+to\s+use|what\s+can\s+you\s+do|menu)\b', msg):
        return 'general_help'

    # 10. Fallback: If currently in booking flow, treat message as selection input
    if booking_step:
        if booking_step == 'AWAITING_CHILD':
            return 'select_child'
        elif booking_step == 'AWAITING_HOSPITAL':
            return 'select_hospital'
        elif booking_step == 'AWAITING_VACCINE':
            return 'select_vaccine'
        elif booking_step == 'AWAITING_DATE':
            return 'select_date'
        elif booking_step == 'AWAITING_SLOT':
            return 'select_slot'

    return 'unknown'



# ---------------------------------------------------------------------------
# Entity Extraction Helpers
# ---------------------------------------------------------------------------

def extract_child_age_days(text: str) -> tuple[int | None, str]:
    """
    Extracts age expressions like '9 months old', '6 weeks', '2 years'
    and converts to total age in days and a display label.
    """
    pattern = r'(\d+)\s*(months?|mths?|mos?|weeks?|wks?|years?|yrs?|days?)\s*(?:old)?'
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None, ""
    
    val = int(match.group(1))
    unit = match.group(2).lower()
    
    if 'month' in unit or 'mth' in unit or 'mo' in unit:
        days = val * 30
        label = f"{val} Month{'s' if val > 1 else ''}"
    elif 'week' in unit or 'wk' in unit:
        days = val * 7
        label = f"{val} Week{'s' if val > 1 else ''}"
    elif 'year' in unit or 'yr' in unit:
        days = val * 365
        label = f"{val} Year{'s' if val > 1 else ''}"
    else:
        days = val
        label = f"{val} Day{'s' if val > 1 else ''}"

    return days, label


def extract_matched_vaccine_key(text: str) -> str | None:
    """Matches text against verified vaccine aliases."""
    text_clean = text.lower().strip()
    
    # Order from most specific multi-word to generic
    aliases = [
        ('pentavalent', ['pentavalent', 'penta', '5 in 1', 'dpt-hepb-hib']),
        ('rotavirus', ['rotavirus', 'rotavac', 'rotateq', 'rotarix', 'rota']),
        ('pcv', ['pcv', 'pneumococcal', 'pneumonia vaccine']),
        ('hepb', ['hepatitis b', 'hepb', 'hep b', 'hepatitis-b']),
        ('hepa', ['hepatitis a', 'hepa', 'hep a', 'hepatitis-a']),
        ('mmr', ['mmr', 'measles mumps rubella', 'mr vaccine', 'measles', 'rubella', 'mumps', 'mr-1', 'mr-2', 'mmr-1', 'mmr-2']),
        ('opv', ['opv', 'oral polio', 'polio drops', 'polio vaccine', 'polio']),
        ('ipv', ['fipv', 'ipv', 'inactivated polio']),
        ('bcg', ['bcg', 'tuberculosis vaccine', 'tb vaccine']),
        ('je', ['japanese encephalitis', 'je vaccine', 'je-1', 'je-2']),
        ('dpt', ['dpt', 'dtap', 'whooping cough vaccine', 'dpt booster']),
        ('td', ['td vaccine', 'tetanus diphtheria', 'tetanus toxoid', 'tetanus', 'tt']),
        ('varicella', ['varicella', 'chickenpox']),
        ('typhoid', ['typhoid', 'tcv'])
    ]

    for key, tokens in aliases:
        for t in tokens:
            # Word boundary search
            if re.search(r'\b' + re.escape(t) + r'\b', text_clean):
                return key
    return None


def extract_matched_hospital(text: str, hospital_qs) -> Hospitaltbl | None:
    """Matches text against existing hospitals in the database."""
    text_clean = text.lower().strip()
    
    # Try exact match or ID match first
    if text_clean.isdigit():
        h = hospital_qs.filter(id=int(text_clean)).first()
        if h:
            return h

    for h in hospital_qs:
        title_lower = h.title.lower()
        if title_lower == text_clean or title_lower in text_clean or text_clean in title_lower:
            return h
        
        # Word overlap
        title_words = set(title_lower.split())
        text_words = set(text_clean.split())
        common = title_words.intersection(text_words)
        # Exclude common stop words
        common_meaningful = [w for w in common if w not in {'hospital', 'clinic', 'center', 'the', 'at', 'in', 'and'}]
        if common_meaningful:
            return h

    return None


def extract_date_from_text(text: str) -> datetime.date | None:
    """
    Extracts date from text supporting:
    - 'today', 'tomorrow', 'day after tomorrow'
    - 'YYYY-MM-DD', 'DD-MM-YYYY', 'DD/MM/YYYY', 'YYYY/MM/DD'
    - 'September 10', '10 September 2026', '10th Sept'
    """
    text_clean = text.strip().lower()
    today = datetime.date.today()

    if 'today' in text_clean:
        return today
    if 'tomorrow' in text_clean:
        return today + datetime.timedelta(days=1)
    if 'day after tomorrow' in text_clean:
        return today + datetime.timedelta(days=2)

    # Standard numeric date formats
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y'):
        match = re.search(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', text_clean)
        if match:
            try:
                return datetime.datetime.strptime(match.group(0), fmt).date()
            except ValueError:
                pass

    # Month name parsing e.g. "September 10", "10 Sep 2026", "Sept 10"
    month_regex = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
    
    # Pattern: Month Day (Year) e.g., "September 10" or "Sep 10 2026"
    m1 = re.search(rf'({month_regex})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{{4}}))?', text_clean)
    if m1:
        month_str = m1.group(1)
        day_str = m1.group(2)
        year_str = m1.group(3) or str(today.year)
        for m_fmt in ('%B', '%b'):
            try:
                dt = datetime.datetime.strptime(f"{month_str} {day_str} {year_str}", f"{m_fmt} %d %Y").date()
                if dt < today and not m1.group(3):
                    # Default to next year if date has already passed this year
                    dt = datetime.datetime.strptime(f"{month_str} {day_str} {today.year + 1}", f"{m_fmt} %d %Y").date()
                return dt
            except ValueError:
                pass

    # Pattern: Day Month (Year) e.g., "10th September 2026"
    m2 = re.search(rf'(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_regex})(?:\s*,?\s*(\d{{4}}))?', text_clean)
    if m2:
        day_str = m2.group(1)
        month_str = m2.group(2)
        year_str = m2.group(3) or str(today.year)
        for m_fmt in ('%B', '%b'):
            try:
                dt = datetime.datetime.strptime(f"{day_str} {month_str} {year_str}", f"%d {m_fmt} %Y").date()
                if dt < today and not m2.group(3):
                    dt = datetime.datetime.strptime(f"{day_str} {month_str} {today.year + 1}", f"%d {m_fmt} %Y").date()
                return dt
            except ValueError:
                pass

    return None


def extract_time_slot_from_text(text: str) -> datetime.time | None:
    """
    Extracts time slot from text like '10:30 AM', '11:00', '2:30 pm'.
    """
    text_clean = text.strip()
    time_match = re.search(r'\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b', text_clean, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        meridiem = time_match.group(3)

        if meridiem:
            meridiem = meridiem.lower()
            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
        try:
            return datetime.time(hour, minute)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Core Dialog Handler
# ---------------------------------------------------------------------------

def process_ai_message(patient_id: int | None, message: str, context: dict | None = None) -> dict:
    """
    Primary entry point to process incoming patient messages.
    Returns:
    {
        'text': str,
        'action_type': str, # 'NONE' | 'SHOW_CHILDREN' | 'SHOW_HOSPITALS' | 'SHOW_VACCINES' | 'SHOW_SLOTS' | 'SHOW_CONFIRMATION' | 'BOOKING_SUCCESS'
        'action_data': dict,
        'context': dict,
        'is_safety_disclaimer': bool
    }
    """
    if context is None:
        context = {}

    msg = message.strip()
    if not msg:
        return {
            'text': "Hello! How can I assist you with child vaccinations or appointments today?",
            'action_type': 'NONE',
            'action_data': {},
            'context': context,
            'is_safety_disclaimer': False
        }

    # Fetch patient profile and children if logged in
    patient = None
    children_qs = Childtbl.objects.none()
    if patient_id:
        patient = Patienttbl.objects.filter(id=patient_id).first()
        if patient:
            children_qs = Childtbl.objects.filter(patient=patient).order_by('dob')

    intent = detect_intent(msg, context)

    # 1. Handle Medical Symptom / Emergency Safety Warning
    if intent == 'medical_symptom_safety':
        return handle_symptom_safety(msg, context)

    # 2. Handle Vaccine Educational Queries
    if intent == 'vaccine_information':
        return handle_vaccine_information_query(msg, context)

    # 3. Handle Child Vaccination Guidance / Recommendations
    if intent == 'upcoming_vaccine':
        return handle_upcoming_vaccines_query(msg, patient, children_qs, context)

    # 4. Handle Appointment Status Inquiry
    if intent == 'appointment_status':
        return handle_appointment_status_query(patient, context)

    # 5. Handle General Help / Greeting
    if intent == 'general_help':
        return handle_general_help(patient, children_qs, context)

    # 6. Handle Conversational Booking Flow (including state transitions & shortcuts)
    return handle_conversational_booking(msg, intent, patient, children_qs, context)


# ---------------------------------------------------------------------------
# Intent Handlers
# ---------------------------------------------------------------------------

def handle_symptom_safety(message: str, context: dict) -> dict:
    """Provides medical safety boundary response when acute symptoms are mentioned."""
    return {
        'text': (
            "🚨 **Important Medical Safety Notice**\n\n"
            "I cannot determine whether your child should receive a vaccine while experiencing acute symptoms "
            "(such as high fever, respiratory distress, convulsions, or severe illness).\n\n"
            "**Recommended Action**:\n"
            "• Please consult your pediatrician or primary healthcare provider immediately before proceeding with vaccination.\n"
            "• If this is a medical emergency, please visit the nearest hospital emergency department.\n\n"
            f"{MEDICAL_SAFETY_DISCLAIMER}"
        ),
        'action_type': 'NONE',
        'action_data': {},
        'context': context,
        'is_safety_disclaimer': True
    }


def handle_vaccine_information_query(message: str, context: dict) -> dict:
    """Answers factual vaccine queries using verified medical knowledge base."""
    matched_key = extract_matched_vaccine_key(message)

    if matched_key and matched_key in VACCINE_KNOWLEDGE_BASE:
        v_info = VACCINE_KNOWLEDGE_BASE[matched_key]
        response_text = (
            f"💉 **{v_info['name']}**\n\n"
            f"• **Vaccine Type**: {v_info['type']}\n"
            f"• **Protects Against**: {v_info['prevents']}\n"
            f"• **Purpose**: {v_info['purpose']}\n"
            f"• **Routine Schedule**: {v_info['schedule']}\n"
            f"• **Aftercare & Expected Reactions**: {v_info['aftercare']}\n\n"
            f"{MEDICAL_SAFETY_DISCLAIMER}"
        )
        return {
            'text': response_text,
            'action_type': 'SHOW_QUICK_ACTIONS',
            'action_data': {
                'quick_replies': [
                    {'label': f'Book {matched_key.upper()}', 'action': f'Book {matched_key.upper()} vaccine'},
                    {'label': 'Upcoming Vaccines', 'action': 'What vaccines are upcoming?'},
                    {'label': 'Ask Another Vaccine', 'action': 'Tell me about PCV vaccine'}
                ]
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    # General overview if no specific vaccine was named
    overview_text = (
        "💉 **Pediatric Immunization Overview**\n\n"
        "Vaccines safely stimulate a child's immune system by producing targeted antibodies against dangerous "
        "bacterial and viral illnesses without causing the disease itself.\n\n"
        "Key routine vaccines in the immunization schedule include:\n"
        "• **BCG & Hepatitis B**: Given at birth\n"
        "• **OPV, Pentavalent, Rotavirus, PCV, fIPV**: Primary series at 6, 10, and 14 weeks\n"
        "• **MR / MMR & PCV Booster**: 9–12 months and 16–24 months\n"
        "• **DPT & Td Boosters**: 5–6 years and 10/16 years\n\n"
        "You can ask me specific questions like *'What is MMR?'*, *'Why is Hepatitis B given?'*, or *'What does polio vaccine prevent?'*.\n\n"
        f"{MEDICAL_SAFETY_DISCLAIMER}"
    )
    return {
        'text': overview_text,
        'action_type': 'SHOW_QUICK_ACTIONS',
        'action_data': {
            'quick_replies': [
                {'label': 'What is BCG?', 'action': 'What is BCG?'},
                {'label': 'What is MMR?', 'action': 'What is MMR?'},
                {'label': 'What is PCV?', 'action': 'What is PCV?'},
                {'label': 'Why Hepatitis B?', 'action': 'Why is Hepatitis B vaccine given?'}
            ]
        },
        'context': context,
        'is_safety_disclaimer': False
    }


def handle_upcoming_vaccines_query(message: str, patient: Patienttbl | None, children_qs, context: dict) -> dict:
    """
    Evaluates upcoming and due vaccines based on child age mentioned or registered child profiles.
    """
    age_days, age_label = extract_child_age_days(message)

    # Scenario A: User asked about a specific age milestone e.g., "My child is 9 months old. What vaccine is due?"
    if age_days is not None:
        milestone_vaccines = []
        for min_days, m_label, vac_list in UIP_MILESTONES:
            # Check milestone closest to or due at this age
            if abs(age_days - min_days) <= 45 or (age_days >= min_days and min_days > (age_days - 90)):
                milestone_vaccines.append((m_label, vac_list))

        if not milestone_vaccines:
            # Fallback: all milestones up to this age
            for min_days, m_label, vac_list in UIP_MILESTONES:
                if age_days >= min_days:
                    milestone_vaccines = [(m_label, vac_list)]

        vaccines_text_lines = []
        for m_label, vac_list in milestone_vaccines:
            vaccines_text_lines.append(f"**Milestone: {m_label}**")
            for v_name in vac_list:
                vaccines_text_lines.append(f"  • {v_name}")

        rec_body = "\n".join(vaccines_text_lines)
        response_text = (
            f"📋 **Personalized Vaccination Recommendation ({age_label})**\n\n"
            f"Based on the Universal Immunization Schedule for an age of **{age_label}**, the following vaccines are due or upcoming:\n\n"
            f"{rec_body}\n\n"
            f"Would you like to check hospital availability and schedule an appointment?\n\n"
            f"{MEDICAL_SAFETY_DISCLAIMER}"
        )
        return {
            'text': response_text,
            'action_type': 'SHOW_QUICK_ACTIONS',
            'action_data': {
                'quick_replies': [
                    {'label': 'Book Appointment', 'action': 'Book a vaccination appointment'},
                    {'label': 'What is MR / MMR?', 'action': 'What is MMR vaccine?'},
                    {'label': 'Check Other Age', 'action': 'What vaccine is due at 6 weeks?'}
                ]
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    # Scenario B: User is logged in and has registered children
    if patient and children_qs.exists():
        # Check if a specific child name was mentioned
        target_child = None
        for child in children_qs:
            if re.search(r'\b' + re.escape(child.childname.lower()) + r'\b', message.lower()):
                target_child = child
                break
        
        if not target_child and children_qs.count() == 1:
            target_child = children_qs.first()

        if target_child:
            return generate_child_schedule_analysis(target_child, context)

        # Multiple children: ask parent which child to analyze
        children_list = [
            {'id': c.id, 'name': c.childname, 'dob': c.dob.strftime('%b %d, %Y'), 'age_years': c.age}
            for c in children_qs
        ]
        return {
            'text': (
                "👶 **Select a Child for Immunization Schedule Analysis**\n\n"
                "I found registered children under your account. Which child would you like me to analyze?"
            ),
            'action_type': 'SHOW_CHILDREN',
            'action_data': {
                'children': children_list,
                'purpose': 'guidance'
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    # Scenario C: Guest / Not logged in without specific age
    return {
        'text': (
            "📋 **Immunization Schedule Analysis**\n\n"
            "To give you an accurate vaccination recommendation, please tell me your child's age "
            "(for example: *'My child is 9 months old'*, *'6 weeks old'*, or *'18 months'*).\n\n"
            "If you have an account, please log in so I can check your child's verified medical history!\n\n"
            f"{MEDICAL_SAFETY_DISCLAIMER}"
        ),
        'action_type': 'NONE',
        'action_data': {},
        'context': context,
        'is_safety_disclaimer': False
    }


def generate_child_schedule_analysis(child: Childtbl, context: dict) -> dict:
    """Builds a detailed Immunization Schedule Analysis for a specific registered child."""
    today = datetime.date.today()
    age_days = (today - child.dob).days if child.dob else 0

    due_vaccines = get_recommended_vaccines(child.id)
    missed_data = get_missed_vaccines(child.id)
    recorded_apts = Appointmenttbl.objects.filter(child_id=child.id).exclude(active=Appointmenttbl.STATUS_CANCELLED).select_related('vaccineid')

    sections = []
    
    # 1. Due / Upcoming
    if due_vaccines:
        due_lines = [f"• **{v.vaccineName}** ({getattr(v, 'due_stage', 'Due')})" for v in due_vaccines[:6]]
        sections.append("🟢 **Due / Recommended Vaccinations**:\n" + "\n".join(due_lines))
    else:
        sections.append("🟢 **Due Vaccinations**: All compulsory milestone vaccines up to current age are up-to-date!")

    # 2. Overdue / Missed
    if missed_data.get('missed'):
        missed_lines = [f"• **{m['name']}** ({m['due_age_range']})" for m in missed_data['missed'][:4]]
        sections.append("🟡 **Potentially Overdue Milestones**:\n" + "\n".join(missed_lines))

    # 3. Recorded History
    if recorded_apts.exists():
        history_lines = [f"• {apt.vaccineid.vaccineName if apt.vaccineid else 'Vaccine'} — {apt.aptdate.strftime('%b %d, %Y') if apt.aptdate else 'Recorded'} ({apt.status_label})" for apt in recorded_apts[:4]]
        sections.append("📋 **Recent Records**:\n" + "\n".join(history_lines))

    body = "\n\n".join(sections)
    response_text = (
        f"📊 **Immunization Schedule Analysis — {child.childname}**\n"
        f"• **Date of Birth**: {child.dob.strftime('%d %B %Y') if child.dob else 'N/A'} (~{age_days // 30} months old)\n\n"
        f"{body}\n\n"
        f"Would you like to book an appointment for {child.childname}?\n\n"
        f"{MEDICAL_SAFETY_DISCLAIMER}"
    )

    return {
        'text': response_text,
        'action_type': 'SHOW_QUICK_ACTIONS',
        'action_data': {
            'quick_replies': [
                {'label': f'Book for {child.childname}', 'action': f'Book appointment for {child.childname}'},
                {'label': 'View Appointments', 'action': 'Check my appointments'},
                {'label': 'Ask About Vaccine', 'action': 'Tell me about MR vaccine'}
            ]
        },
        'context': context,
        'is_safety_disclaimer': False
    }


def handle_appointment_status_query(patient: Patienttbl | None, context: dict) -> dict:
    """Checks and reports upcoming and past appointments for logged-in patient."""
    if not patient:
        return {
            'text': "Please log in to your KiddoVax account to check your booked appointments and vaccination history.",
            'action_type': 'NONE',
            'action_data': {},
            'context': context,
            'is_safety_disclaimer': False
        }

    appointments = Appointmenttbl.objects.filter(patientid=patient).select_related('hospitalid', 'vaccineid', 'child').order_by('-aptdate')[:5]

    if not appointments.exists():
        return {
            'text': (
                "📅 **My Appointments**\n\n"
                "You currently have no recorded appointments in the system.\n"
                "Would you like me to help you schedule a vaccination appointment?"
            ),
            'action_type': 'SHOW_QUICK_ACTIONS',
            'action_data': {
                'quick_replies': [
                    {'label': 'Book Appointment', 'action': 'Book a vaccination appointment'},
                    {'label': 'Check Due Vaccines', 'action': 'What vaccine is due for my child?'}
                ]
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    lines = []
    for apt in appointments:
        child_label = apt.display_child_name
        vaccine_label = apt.vaccineid.vaccineName if apt.vaccineid else 'Vaccine'
        hosp_label = apt.hospitalid.title if apt.hospitalid else 'Hospital'
        date_label = apt.aptdate.strftime('%d %b %Y') if apt.aptdate else 'Date TBD'
        time_label = f" at {apt.apttime.strftime('%I:%M %p')}" if apt.apttime else ""
        lines.append(f"• **{vaccine_label}** for **{child_label}**\n  🏥 {hosp_label}\n  📅 {date_label}{time_label}\n  🔖 Status: `{apt.status_label}`")

    body = "\n\n".join(lines)
    return {
        'text': f"📅 **Your Appointments**\n\n{body}\n\nNeed to schedule another appointment or ask a question?",
        'action_type': 'SHOW_QUICK_ACTIONS',
        'action_data': {
            'quick_replies': [
                {'label': 'Book New Appointment', 'action': 'Book a vaccination appointment'},
                {'label': 'Vaccine Information', 'action': 'What is MMR?'}
            ]
        },
        'context': context,
        'is_safety_disclaimer': False
    }


def handle_general_help(patient: Patienttbl | None, children_qs, context: dict) -> dict:
    """Friendly greeting and capabilities summary."""
    name_str = f" {patient.name}" if patient else ""
    help_text = (
        f"👋 **Hello{name_str}! Welcome to the KiddoVax AI Assistant.**\n\n"
        "I am your pediatric vaccination and immunization appointment assistant. Here is what I can do for you:\n\n"
        "1. 📖 **Vaccine Information**: Ask me about any childhood vaccine (e.g. *'What is MMR?'*, *'Why Hepatitis B?'*, *'What does Polio vaccine prevent?'*).\n"
        "2. 👶 **Personalized Recommendations**: Ask *'What vaccine is due for my child?'* or *'My child is 9 months old'*, and I'll analyze the immunization schedule.\n"
        "3. 📅 **Conversational Booking**: Say *'Book an appointment'* or *'Book MMR for my child'* to book step-by-step through conversation!\n"
        "4. 🔍 **Appointment Status**: Check your upcoming vaccination visits and queue statuses."
    )
    return {
        'text': help_text,
        'action_type': 'SHOW_QUICK_ACTIONS',
        'action_data': {
            'quick_replies': [
                {'label': 'Book Appointment', 'action': 'Book a vaccination appointment'},
                {'label': 'Upcoming Vaccines', 'action': 'What vaccine is due for my child?'},
                {'label': 'What is MMR?', 'action': 'What is MMR?'},
                {'label': 'My Appointments', 'action': 'Check my appointments'}
            ]
        },
        'context': context,
        'is_safety_disclaimer': False
    }


# ---------------------------------------------------------------------------
# Conversational Booking State Machine
# ---------------------------------------------------------------------------

def handle_conversational_booking(message: str, intent: str, patient: Patienttbl | None, children_qs, context: dict) -> dict:
    """
    State machine for multi-turn appointment booking:
    States:
    - None / 'INIT': Initializes booking and requests Child or Hospital.
    - 'AWAITING_CHILD': Select child.
    - 'AWAITING_HOSPITAL': Select hospital.
    - 'AWAITING_VACCINE': Select vaccine from chosen hospital inventory.
    - 'AWAITING_DATE': Select appointment date.
    - 'AWAITING_SLOT': Select time slot.
    - 'AWAITING_CONFIRMATION': User confirms booking.
    """
    booking_ctx = context.get('booking_ctx', {})
    current_step = context.get('booking_step')

    # Handle Cancellation
    if intent == 'cancel_booking':
        context['booking_step'] = None
        context['booking_ctx'] = {}
        return {
            'text': "❌ Appointment booking has been cancelled. Let me know whenever you'd like to book or ask another question!",
            'action_type': 'NONE',
            'action_data': {},
            'context': context,
            'is_safety_disclaimer': False
        }

    # -----------------------------------------------------------------------
    # Initial / Fast-Forward Entity Extraction
    # -----------------------------------------------------------------------
    # Extract any entities present in the current utterance
    # 1. Child extraction
    if not booking_ctx.get('child_id'):
        for child in children_qs:
            if re.search(r'\b' + re.escape(child.childname.lower()) + r'\b', message.lower()):
                booking_ctx['child_id'] = child.id
                booking_ctx['child_name'] = child.childname
                break

    # 2. Vaccine extraction
    if not booking_ctx.get('vaccine_id'):
        v_key = extract_matched_vaccine_key(message)
        if v_key:
            # Look up matching vaccine in DB
            matched_v = Vaccinetbl.objects.filter(vaccineName__icontains=v_key).first()
            if matched_v:
                booking_ctx['vaccine_key'] = v_key
                booking_ctx['vaccine_name'] = matched_v.vaccineName
                if booking_ctx.get('hospital_id'):
                    # Match specific hospital vaccine
                    h_vac = Vaccinetbl.objects.filter(hospitalId_id=booking_ctx['hospital_id'], vaccineName__icontains=v_key).first()
                    if h_vac:
                        booking_ctx['vaccine_id'] = h_vac.id
                        booking_ctx['vaccine_name'] = h_vac.vaccineName

    # 3. Hospital extraction
    if not booking_ctx.get('hospital_id'):
        all_hospitals = Hospitaltbl.objects.all()
        matched_h = extract_matched_hospital(message, all_hospitals)
        if matched_h:
            booking_ctx['hospital_id'] = matched_h.id
            booking_ctx['hospital_name'] = matched_h.title

    # 4. Date extraction
    if not booking_ctx.get('apt_date'):
        parsed_d = extract_date_from_text(message)
        if parsed_d:
            if parsed_d < datetime.date.today():
                return {
                    'text': "⚠️ The date you specified is in the past. Please select today or a future date for your appointment.",
                    'action_type': 'NONE',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }
            booking_ctx['apt_date'] = parsed_d.strftime('%Y-%m-%d')

    # 5. Time extraction
    if not booking_ctx.get('apt_time'):
        parsed_t = extract_time_slot_from_text(message)
        if parsed_t:
            booking_ctx['apt_time'] = parsed_t.strftime('%H:%M:%S')
            booking_ctx['apt_time_str'] = parsed_t.strftime('%I:%M %p')

    # -----------------------------------------------------------------------
    # Transition State Logic
    # -----------------------------------------------------------------------

    # STEP 1: Child Selection
    if not booking_ctx.get('child_id') and not booking_ctx.get('child_name'):
        if patient and children_qs.exists():
            if children_qs.count() == 1:
                # Auto-select only child
                single_child = children_qs.first()
                booking_ctx['child_id'] = single_child.id
                booking_ctx['child_name'] = single_child.childname
            else:
                # Ask user to pick child
                context['booking_step'] = 'AWAITING_CHILD'
                context['booking_ctx'] = booking_ctx
                child_list = [
                    {'id': c.id, 'name': c.childname, 'dob': c.dob.strftime('%b %d, %Y'), 'age_years': c.age}
                    for c in children_qs
                ]
                return {
                    'text': "👶 **Step 1 of 5: Select Child**\n\nWhich child would you like to book this vaccination appointment for?",
                    'action_type': 'SHOW_CHILDREN',
                    'action_data': {'children': child_list},
                    'context': context,
                    'is_safety_disclaimer': False
                }
        else:
            # Guest / No registered child: ask for child name
            if intent == 'select_child' or current_step == 'AWAITING_CHILD':
                clean_name = re.sub(r'^(?:for|child|name is|book for)\s+', '', message, flags=re.IGNORECASE).strip()
                if clean_name:
                    booking_ctx['child_name'] = clean_name.title()
                else:
                    booking_ctx['child_name'] = "Child Profile"
            else:
                context['booking_step'] = 'AWAITING_CHILD'
                context['booking_ctx'] = booking_ctx
                return {
                    'text': "👶 **Step 1 of 5: Child Name**\n\nPlease provide your child's name to proceed with booking:",
                    'action_type': 'NONE',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }

    # STEP 2: Hospital Selection
    if not booking_ctx.get('hospital_id'):
        if intent == 'select_hospital' or current_step == 'AWAITING_HOSPITAL':
            all_hospitals = Hospitaltbl.objects.all().order_by('-id')
            matched_h = extract_matched_hospital(message, all_hospitals)
            if matched_h:
                booking_ctx['hospital_id'] = matched_h.id
                booking_ctx['hospital_name'] = matched_h.title
            else:
                context['booking_step'] = 'AWAITING_HOSPITAL'
                context['booking_ctx'] = booking_ctx
                h_list = [{'id': h.id, 'title': h.title, 'address': h.address} for h in all_hospitals[:10]]

                return {
                    'text': (
                        f"🏥 I couldn't find a hospital matching '{message}'.\n\n"
                        "Please select one of our available vaccination centers:"
                    ),
                    'action_type': 'SHOW_HOSPITALS',
                    'action_data': {'hospitals': h_list},
                    'context': context,
                    'is_safety_disclaimer': False
                }
        else:
            context['booking_step'] = 'AWAITING_HOSPITAL'
            context['booking_ctx'] = booking_ctx
            all_hospitals = Hospitaltbl.objects.all().order_by('-id')
            h_list = [{'id': h.id, 'title': h.title, 'address': h.address} for h in all_hospitals[:10]]

            child_str = booking_ctx.get('child_name', 'your child')
            return {
                'text': f"🏥 **Step 2 of 5: Select Hospital**\n\nWhich hospital/clinic would you like to visit for **{child_str}**?",
                'action_type': 'SHOW_HOSPITALS',
                'action_data': {'hospitals': h_list},
                'context': context,
                'is_safety_disclaimer': False
            }

    # STEP 3: Vaccine Selection
    hosp_id = booking_ctx['hospital_id']
    if not booking_ctx.get('vaccine_id'):
        avail_vaccines = Vaccinetbl.objects.filter(hospitalId_id=hosp_id).order_by('vaccineName')
        if not avail_vaccines.exists():
            avail_vaccines = Vaccinetbl.objects.all().order_by('vaccineName')

        if intent == 'select_vaccine' or current_step == 'AWAITING_VACCINE' or booking_ctx.get('vaccine_key'):
            v_key = booking_ctx.get('vaccine_key') or extract_matched_vaccine_key(message)
            matched_v = None
            if v_key:
                matched_v = avail_vaccines.filter(vaccineName__icontains=v_key).first()
            if not matched_v and message.isdigit():
                matched_v = avail_vaccines.filter(id=int(message)).first()
            if not matched_v:
                # Substring match on vaccine name
                for v in avail_vaccines:
                    if v.vaccineName.lower() in message.lower() or message.lower() in v.vaccineName.lower():
                        matched_v = v
                        break

            if matched_v:
                booking_ctx['vaccine_id'] = matched_v.id
                booking_ctx['vaccine_name'] = matched_v.vaccineName
            else:
                context['booking_step'] = 'AWAITING_VACCINE'
                context['booking_ctx'] = booking_ctx
                v_list = [{'id': v.id, 'name': v.vaccineName, 'price': v.price or 0} for v in avail_vaccines[:10]]
                return {
                    'text': (
                        f"💉 Vaccine '{message}' is not recognized or currently out of stock at **{booking_ctx.get('hospital_name')}**.\n\n"
                        "Please select from available vaccines below:"
                    ),
                    'action_type': 'SHOW_VACCINES',
                    'action_data': {'vaccines': v_list},
                    'context': context,
                    'is_safety_disclaimer': False
                }
        else:
            context['booking_step'] = 'AWAITING_VACCINE'
            context['booking_ctx'] = booking_ctx
            v_list = [{'id': v.id, 'name': v.vaccineName, 'price': v.price or 0} for v in avail_vaccines[:10]]
            return {
                'text': f"💉 **Step 3 of 5: Select Vaccine**\n\nWhich vaccine would you like to book at **{booking_ctx.get('hospital_name')}**?",
                'action_type': 'SHOW_VACCINES',
                'action_data': {'vaccines': v_list},
                'context': context,
                'is_safety_disclaimer': False
            }

    # STEP 4: Date Selection
    if not booking_ctx.get('apt_date'):
        parsed_d = extract_date_from_text(message)
        if parsed_d:
            if parsed_d < datetime.date.today():
                return {
                    'text': "⚠️ The appointment date cannot be in the past. Please select a valid upcoming date.",
                    'action_type': 'NONE',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }
            # Check hospital holiday
            if HospitalHoliday.objects.filter(hospital_id=hosp_id, date=parsed_d).exists():
                hol = HospitalHoliday.objects.filter(hospital_id=hosp_id, date=parsed_d).first()
                return {
                    'text': f"⚠️ **{booking_ctx.get('hospital_name')}** is closed on {parsed_d.strftime('%d %B %Y')} ({hol.description or 'Holiday'}). Please choose another date.",
                    'action_type': 'NONE',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }
            booking_ctx['apt_date'] = parsed_d.strftime('%Y-%m-%d')
        else:
            context['booking_step'] = 'AWAITING_DATE'
            context['booking_ctx'] = booking_ctx
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            day_after = datetime.date.today() + datetime.timedelta(days=2)
            return {
                'text': (
                    "📅 **Step 4 of 5: Select Appointment Date**\n\n"
                    "When would you like to schedule the visit? You can type a date (e.g. *'Tomorrow'*, *'September 10'*, or *'2026-09-15'*)."
                ),
                'action_type': 'SHOW_DATE_PICKER',
                'action_data': {
                    'suggested_dates': [
                        {'label': f"Tomorrow ({tomorrow.strftime('%d %b')})", 'date': tomorrow.strftime('%Y-%m-%d')},
                        {'label': f"Day After ({day_after.strftime('%d %b')})", 'date': day_after.strftime('%Y-%m-%d')}
                    ]
                },
                'context': context,
                'is_safety_disclaimer': False
            }

    # STEP 5: Time Slot Selection
    date_val = datetime.datetime.strptime(booking_ctx['apt_date'], '%Y-%m-%d').date()
    if not booking_ctx.get('apt_time'):
        parsed_t = extract_time_slot_from_text(message)
        if parsed_t:
            booking_ctx['apt_time'] = parsed_t.strftime('%H:%M:%S')
            booking_ctx['apt_time_str'] = parsed_t.strftime('%I:%M %p')
        else:
            context['booking_step'] = 'AWAITING_SLOT'
            context['booking_ctx'] = booking_ctx
            # Generate available dynamic slots from booking_service
            slots = generate_hospital_time_slots(hosp_id, date_val)
            avail_slots = [s for s in slots if s.get('status') == 'AVAILABLE']
            
            if not avail_slots:
                # If no available slots on that date
                context['booking_step'] = 'AWAITING_DATE'
                booking_ctx['apt_date'] = None
                context['booking_ctx'] = booking_ctx
                return {
                    'text': f"⚠️ All time slots at **{booking_ctx.get('hospital_name')}** on {date_val.strftime('%d %b %Y')} are fully booked or unavailable. Please choose another date.",
                    'action_type': 'SHOW_DATE_PICKER',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }

            return {
                'text': (
                    f"⏰ **Step 5 of 5: Select Available Time Slot**\n\n"
                    f"Available slots for **{date_val.strftime('%d %B %Y')}** at **{booking_ctx.get('hospital_name')}**:"
                ),
                'action_type': 'SHOW_SLOTS',
                'action_data': {
                    'date': booking_ctx['apt_date'],
                    'slots': avail_slots
                },
                'context': context,
                'is_safety_disclaimer': False
            }

    # STEP 6: Confirmation Step
    if current_step != 'AWAITING_CONFIRMATION' and intent != 'confirm_booking':
        context['booking_step'] = 'AWAITING_CONFIRMATION'
        context['booking_ctx'] = booking_ctx
        child_label = booking_ctx.get('child_name')
        vac_label = booking_ctx.get('vaccine_name')
        hosp_label = booking_ctx.get('hospital_name')
        date_label = date_val.strftime('%d %B %Y')
        time_label = booking_ctx.get('apt_time_str') or booking_ctx.get('apt_time')

        summary_text = (
            "📋 **Please Confirm Your Appointment Details**:\n\n"
            f"• **Child Profile**: {child_label}\n"
            f"• **Vaccine**: {vac_label}\n"
            f"• **Hospital**: {hosp_label}\n"
            f"• **Date**: {date_label}\n"
            f"• **Time Slot**: {time_label}\n\n"
            "Please reply **'Confirm'** to finalize your booking or **'Cancel'** to abort."
        )

        return {
            'text': summary_text,
            'action_type': 'SHOW_CONFIRMATION',
            'action_data': {
                'booking': booking_ctx
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    # STEP 7: Create Appointment in Database
    if intent == 'confirm_booking' or current_step == 'AWAITING_CONFIRMATION':
        return execute_appointment_creation(patient, booking_ctx, context)

    return {
        'text': "I did not understand your reply. Please type 'Confirm' to book your appointment or 'Cancel' to stop.",
        'action_type': 'NONE',
        'action_data': {},
        'context': context,
        'is_safety_disclaimer': False
    }


def execute_appointment_creation(patient: Patienttbl | None, booking_ctx: dict, context: dict) -> dict:
    """
    Validates capacity and creates a valid Appointmenttbl record using the existing KiddoVax workflow.
    """
    try:
        hosp_id = int(booking_ctx['hospital_id'])
        vac_id = int(booking_ctx['vaccine_id'])
        date_val = datetime.datetime.strptime(booking_ctx['apt_date'], '%Y-%m-%d').date()
        time_val = None
        if booking_ctx.get('apt_time'):
            time_val = datetime.datetime.strptime(booking_ctx['apt_time'], '%H:%M:%S').time()

        # 1. Server-side slot reservation & capacity validation
        validate_and_reserve_slot(hosp_id, date_val, time_val)

        # 2. Check duplicate appointment for child + vaccine
        child_id = booking_ctx.get('child_id')
        child_name = booking_ctx.get('child_name') or "Child Profile"
        
        child_obj = None
        if child_id:
            child_obj = Childtbl.objects.filter(id=child_id).first()

        selected_vac = Vaccinetbl.objects.filter(id=vac_id).first()

        if child_obj and selected_vac:
            from django.db.models import Q
            existing_dup = Appointmenttbl.objects.filter(
                Q(child=child_obj) | Q(childname__iexact=child_obj.childname),
                vaccineid__vaccineName__iexact=selected_vac.vaccineName
            ).exclude(active=Appointmenttbl.STATUS_CANCELLED).first()
            if existing_dup:
                context['booking_step'] = None
                context['booking_ctx'] = {}
                return {
                    'text': f"⚠️ **{child_obj.childname}** already has an active appointment for **{selected_vac.vaccineName}** (Appointment #{existing_dup.id}). Booking was not duplicated.",
                    'action_type': 'NONE',
                    'action_data': {},
                    'context': context,
                    'is_safety_disclaimer': False
                }

        # 3. Create appointment in database
        appointment = Appointmenttbl.objects.create(
            hospitalid_id=hosp_id,
            vaccineid_id=vac_id,
            patientid=patient,
            child=child_obj,
            childname=child_obj.childname if child_obj else child_name,
            aptdate=date_val,
            apttime=time_val,
            active=0 # 0 = BOOKED / PENDING
        )

        # Reset booking context
        context['booking_step'] = 'COMPLETED'
        context['booking_ctx'] = {}

        hosp_title = appointment.hospitalid.title if appointment.hospitalid else booking_ctx.get('hospital_name')
        vac_title = appointment.vaccineid.vaccineName if appointment.vaccineid else booking_ctx.get('vaccine_name')
        time_str = time_val.strftime('%I:%M %p') if time_val else 'Scheduled'

        success_msg = (
            "🎉 **Appointment Successfully Confirmed!**\n\n"
            f"• **Appointment ID**: `#{appointment.id}`\n"
            f"• **Child**: {appointment.display_child_name}\n"
            f"• **Vaccine**: {vac_title}\n"
            f"• **Hospital**: {hosp_title}\n"
            f"• **Date & Time**: {date_val.strftime('%d %B %Y')} at {time_str}\n"
            f"• **Status**: `BOOKED`\n\n"
            "Your appointment is registered in the KiddoVax clinical system. You can view or manage it anytime in your appointments dashboard."
        )

        return {
            'text': success_msg,
            'action_type': 'BOOKING_SUCCESS',
            'action_data': {
                'appointment_id': appointment.id,
                'child_name': appointment.display_child_name,
                'vaccine_name': vac_title,
                'hospital_name': hosp_title,
                'date': date_val.strftime('%Y-%m-%d'),
                'time': time_str
            },
            'context': context,
            'is_safety_disclaimer': False
        }

    except ValidationError as ve:
        context['booking_step'] = 'AWAITING_SLOT'
        return {
            'text': f"⚠️ **Booking Notice**: {str(ve.message if hasattr(ve, 'message') else ve)}\nPlease choose an alternate time or date.",
            'action_type': 'SHOW_SLOTS',
            'action_data': {},
            'context': context,
            'is_safety_disclaimer': False
        }
    except Exception as e:
        return {
            'text': f"❌ An unexpected error occurred while booking: {str(e)}. Please try again or book directly via the Appointments page.",
            'action_type': 'NONE',
            'action_data': {},
            'context': context,
            'is_safety_disclaimer': False
        }
