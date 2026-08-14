import re

VERIFIED_VACCINE_KNOWLEDGE_BASE = {
    'dtap': {
        'title': 'DTaP (Diphtheria, Tetanus, Acellular Pertussis)',
        'purpose': 'Protects children against diphtheria (severe throat infection), tetanus (lockjaw), and pertussis (whooping cough).',
        'why_multiple': 'Multi-dose series (given at 2, 4, 6, 15-18 months, and 4-6 years) are required because antibodies gradually decay and booster doses ensure long-term immunity.',
        'aftercare': 'Mild soreness at injection site or low-grade fever is normal. Apply a cool damp cloth to arm/thigh. Stay hydrated.',
    },
    'mmr': {
        'title': 'MMR (Measles, Mumps, Rubella)',
        'purpose': 'Protects against measles (highly contagious fever & rash), mumps (swollen salivary glands), and rubella (German measles).',
        'why_multiple': 'Dose 1 is administered at 9-12 months and Dose 2 at 15-18 months to achieve >97% lifetime protection.',
        'aftercare': 'Mild rash or fever may occur 7-12 days post-vaccination. Monitor child comfort.',
    },
    'opv': {
        'title': 'OPV / IPV (Polio Vaccine)',
        'purpose': 'Protects children against poliovirus which can cause irreversible muscle paralysis.',
        'why_multiple': 'Administered at birth, 6 wks, 10 wks, and 14 wks to ensure gut and blood immunity against all 3 wild polio strains.',
        'aftercare': 'Extremely safe. Oral drops have virtually no side effects.',
    },
    'bcg': {
        'title': 'BCG (Tuberculosis)',
        'purpose': 'Protects infants against severe tubercular meningitis and disseminated TB.',
        'why_multiple': 'Single dose given at birth or earliest contact.',
        'aftercare': 'A small red papule develops at the injection site after 2-3 weeks, forming a small scar. This is a normal immune response.',
    },
    'hepb': {
        'title': 'Hepatitis B',
        'purpose': 'Prevents chronic Hepatitis B liver infection and liver damage.',
        'why_multiple': 'Dose at birth followed by 6, 10, 14-week combinations ensures 98%+ immunity.',
        'aftercare': 'Slight soreness at injection site.',
    }
}

ACUTE_SYMPTOM_KEYWORDS = [
    'fever above 102', 'high fever', 'breathing difficulty', 'seizure',
    'allergic reaction', 'swelling face', 'unresponsive', 'convulsion',
    'severe pain', 'vomiting', 'diarrhea', 'sick right now', 'should i give'
]


def answer_vaccine_education_query(query_text: str, child_id: int = None) -> dict:
    """
    Answers vaccine educational queries using verified knowledge base.
    Enforces strict medical safety boundaries for symptom inquiries.
    """
    query_clean = query_text.lower().strip()

    # Safety Check: Direct medical decision / symptom request
    for kw in ACUTE_SYMPTOM_KEYWORDS:
        if kw in query_clean:
            return {
                'is_safety_disclaimer': True,
                'title': 'Medical Safety Notice',
                'answer': "I cannot determine whether your child should receive a vaccine based on symptoms alone. Clinical decisions must be made by a qualified healthcare professional.",
                'action_advice': "Please consult your healthcare provider or contact your vaccination hospital before proceeding with vaccination.",
                'show_contact_button': True
            }

    # Match vaccine keywords
    matched_key = None
    if 'dtap' in query_clean or 'pertussis' in query_clean or 'tetanus' in query_clean:
        matched_key = 'dtap'
    elif 'mmr' in query_clean or 'measles' in query_clean or 'mumps' in query_clean or 'rubella' in query_clean:
        matched_key = 'mmr'
    elif 'opv' in query_clean or 'ipv' in query_clean or 'polio' in query_clean:
        matched_key = 'opv'
    elif 'bcg' in query_clean or 'tb' in query_clean or 'tuberculosis' in query_clean:
        matched_key = 'bcg'
    elif 'hep' in query_clean or 'hepatitis' in query_clean:
        matched_key = 'hepb'

    if matched_key:
        kb = VERIFIED_VACCINE_KNOWLEDGE_BASE[matched_key]
        return {
            'is_safety_disclaimer': False,
            'title': kb['title'],
            'answer': f"**Purpose**: {kb['purpose']}\n\n**Why Multiple Doses**: {kb['why_multiple']}\n\n**After-Care**: {kb['aftercare']}",
            'sources': "Official Public Health Immunization Guidelines",
            'show_contact_button': False
        }

    # General explanation for general questions
    return {
        'is_safety_disclaimer': False,
        'title': 'Child Vaccination Guidance',
        'answer': "Vaccines stimulate your child's immune system to recognize and fight specific disease-causing pathogens safely. Adhering to the scheduled age intervals guarantees maximum protection against preventable illnesses.",
        'sources': "Verified KiddoVax Medical Knowledge Base",
        'show_contact_button': False
    }
