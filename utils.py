# utils.py

from translations import translations

# Language state management
user_languages = {}

def get_language(chat_id):
    return user_languages.get(chat_id, 'en')  # Default to English

def set_language(chat_id, language):
    user_languages[chat_id] = language

def translate(chat_id, key):
    """Fetch the translated text for a given key and user's language."""
    lang = get_language(chat_id)
    return translations.get(lang, translations['en']).get(key, '')

from typing import List


def is_nested_empty(lst: List) -> bool:
    """
    This function check if nested list is empty.
    :param lst: List
    :return: bool. True if nested list is empty.
    """
    if not lst:
        return True
    for item in lst:
        if not isinstance(item, list) or not is_nested_empty(item):
            return False
    return True