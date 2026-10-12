import re
import spacy

_nlp = None

def get_spacy_nlp():
    """
    Lazy load spaCy NLP model for sentence tokenization and entity parsing.
    Falls back gracefully to spacy.blank('en') if en_core_web_sm is not loaded.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load('en_core_web_sm')
        except Exception:
            _nlp = spacy.blank('en')
            if 'sentencizer' not in _nlp.pipe_names:
                _nlp.add_pipe('sentencizer')
    return _nlp


def preprocess_context(context):
    """
    Validates and normalizes context text.
    Splits context into sentences while preserving sentence boundaries, punctuation, and entities.
    """
    if not context or not isinstance(context, str):
        return {
            'valid': False,
            'message': 'Context evidence text cannot be empty.',
            'clean_context': '',
            'sentences': []
        }

    clean_context = re.sub(r'\s+', ' ', context).strip()

    if len(clean_context) == 0:
        return {
            'valid': False,
            'message': 'Context evidence text is empty after trimming.',
            'clean_context': '',
            'sentences': []
        }

    if len(clean_context) > 500000:
        return {
            'valid': False,
            'message': 'Context evidence text exceeds maximum limit (500,000 characters).',
            'clean_context': clean_context[:500000],
            'sentences': []
        }

    # Sentence segmentation using spaCy doc
    nlp = get_spacy_nlp()
    doc = nlp(clean_context)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    # Fallback to regex if spaCy sentence splitting yields empty
    if not sentences and clean_context:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_context) if s.strip()]

    return {
        'valid': True,
        'message': 'Context preprocessed successfully.',
        'clean_context': clean_context,
        'sentences': sentences,
        'num_sentences': len(sentences),
        'num_words': len(clean_context.split()),
        'num_chars': len(clean_context)
    }


def preprocess_question(question):
    """
    Validates and normalizes user question.
    Determines question intent type (WHERE, WHEN, WHO, WHICH_ORG, WHAT, HOW_MANY).
    """
    if not question or not isinstance(question, str):
        return {
            'valid': False,
            'message': 'Question cannot be empty.',
            'clean_question': '',
            'qtype': 'UNKNOWN',
            'keywords': []
        }

    clean_q = re.sub(r'\s+', ' ', question).strip()

    if len(clean_q) == 0:
        return {
            'valid': False,
            'message': 'Question is empty after trimming.',
            'clean_question': '',
            'qtype': 'UNKNOWN',
            'keywords': []
        }

    q_lower = clean_q.lower()

    # Determine question type
    if re.search(r'\bwhere\b', q_lower):
        qtype = 'LOCATION'
    elif re.search(r'\b(when|what time|date|day)\b', q_lower):
        qtype = 'DATE_TIME'
    elif re.search(r'\b(who|whose|whom)\b', q_lower):
        qtype = 'PERSON'
    elif re.search(r'\b(organization|company|firm|employer|employed|work for|worked for|agency)\b', q_lower):
        qtype = 'ORGANIZATION'
    elif re.search(r'\b(how many|how much|count)\b', q_lower):
        qtype = 'QUANTITY'
    else:
        qtype = 'GENERAL'

    # Extract clean keywords (excluding stop words and question markers)
    stop_words = {'where', 'when', 'who', 'what', 'which', 'how', 'did', 'does', 'do', 'was', 'were', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'from', 'with', 'by', 'of'}
    words = re.findall(r'\b\w+\b', q_lower)
    keywords = [w for w in words if w not in stop_words and len(w) > 1]

    return {
        'valid': True,
        'message': 'Question preprocessed successfully.',
        'clean_question': clean_q,
        'qtype': qtype,
        'keywords': keywords
    }
