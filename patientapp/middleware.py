from bs4 import BeautifulSoup
from .translations import TRANSLATIONS

class AutoTranslationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only translate 200 OK HTML responses from the patient portal
        if response.status_code == 200 and 'text/html' in response.get('Content-Type', ''):
            lang = request.session.get('django_language', 'en')
            if lang in ['hi', 'gu']:
                trans_dict = TRANSLATIONS.get(lang, {})
                if trans_dict:
                    html_content = response.content.decode('utf-8')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 1. Translate all text nodes (excluding script, style, head, title, etc.)
                    for text_node in soup.find_all(text=True):
                        if text_node.parent.name in ['script', 'style', 'head', 'title']:
                            continue
                        
                        original_str = text_node.string
                        if original_str:
                            stripped = original_str.strip()
                            if stripped in trans_dict:
                                translated_val = trans_dict[stripped]
                                text_node.replace_with(original_str.replace(stripped, translated_val))
                                
                    # 2. Translate input placeholders
                    for tag in soup.find_all(placeholder=True):
                        original_placeholder = tag['placeholder']
                        if original_placeholder:
                            stripped_placeholder = original_placeholder.strip()
                            if stripped_placeholder in trans_dict:
                                tag['placeholder'] = original_placeholder.replace(
                                    stripped_placeholder, 
                                    trans_dict[stripped_placeholder]
                                )
                                
                    # 3. Translate button/input values
                    for tag in soup.find_all('input', type=['submit', 'button']):
                        if tag.has_attr('value') and tag['value']:
                            stripped_val = tag['value'].strip()
                            if stripped_val in trans_dict:
                                tag['value'] = tag['value'].replace(stripped_val, trans_dict[stripped_val])
                                
                    response.content = str(soup).encode('utf-8')
                    
        return response
