import re
import uuid
from datetime import datetime

PRONOUN_MAP = {
    "he": ["PERSON"],
    "him": ["PERSON"],
    "his": ["PERSON"],
    "she": ["PERSON"],
    "her": ["PERSON"],
    "hers": ["PERSON"],
    "they": ["PERSON", "ORGANIZATION"],
    "them": ["PERSON", "ORGANIZATION"],
    "their": ["PERSON", "ORGANIZATION"],
    "there": ["LOCATION"],
    "here": ["LOCATION"],
    "it": ["ORGANIZATION", "LOCATION", "QUANTITY", "DATE_TIME"]
}

def generate_session_id():
    """Generates a unique session identifier."""
    return f"session_{uuid.uuid4().hex[:10]}"

def get_current_timestamp():
    """Returns ISO formatted current timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sanitize_input(text):
    """Sanitizes user input string."""
    if not text:
        return ""
    return text.strip()

def contains_pronoun(question):
    """Checks if question contains pronouns needing multi-turn resolution."""
    words = re.findall(r'\b[a-zA-Z]+\b', question.lower())
    for w in words:
        if w in PRONOUN_MAP:
            return True
    return False

def extract_entities_from_text(text):
    """
    Extracts basic named entities using regex patterns for session memory cache.
    """
    if not text:
        return {}

    entities = {
        'PERSON': [],
        'LOCATION': [],
        'ORGANIZATION': [],
        'DATE_TIME': []
    }

    # Capitalized Words / Names
    persons = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text)
    if persons:
        entities['PERSON'] = list(set(persons))

    # Dates
    dates = re.findall(r'\b(?:\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4})\b', text)
    if dates:
        entities['DATE_TIME'] = list(set(dates))

    return entities
