from .translations import TRANSLATIONS

def translation_processor(request):
    lang = request.session.get('django_language', 'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    return {
        'CURRENT_LANG': lang,
        'T': TRANSLATIONS[lang]
    }
