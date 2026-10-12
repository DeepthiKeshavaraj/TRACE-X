import os
import json
import joblib
import spacy
import sklearn_crfsuite

RAW_NER_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'ner')
PROCESSED_NER_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'ner')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

MODEL_PATH = os.path.join(MODEL_DIR, 'crf_ner_model.pkl')
STATS_PATH = os.path.join(PROCESSED_NER_DIR, 'ner_stats.json')

VALID_BIO_TAGS = {'O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-MISC', 'I-MISC'}
TAG_TO_CATEGORY = {
    'PER': 'PERSON',
    'ORG': 'ORGANIZATION',
    'LOC': 'LOCATION',
    'MISC': 'MISCELLANEOUS'
}

# Lazy load spaCy model
_nlp = None

def get_spacy_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load('en_core_web_sm')
        except Exception:
            _nlp = spacy.blank('en')
            if 'sentencizer' not in _nlp.pipe_names:
                _nlp.add_pipe('sentencizer')
    return _nlp


def raw_iob1_to_iob2(sent):
    """
    Converts raw IOB1 format (where first token of entity gets I- unless preceding token is same type)
    into standard IOB2 format (where first token of every entity gets B-).
    """
    iob2_sent = []
    prev_type = None

    for item in sent:
        token = item['token']
        pos = item['pos']
        tag = item['label']

        if tag == 'O':
            new_tag = 'O'
            prev_type = None
        else:
            tag_parts = tag.split('-')
            prefix = tag_parts[0]
            ent_type = tag_parts[1] if len(tag_parts) > 1 else 'MISC'

            if ent_type not in TAG_TO_CATEGORY:
                ent_type = 'MISC'

            if prefix == 'B':
                new_tag = f"B-{ent_type}"
            elif prefix == 'I':
                if prev_type != ent_type:
                    new_tag = f"B-{ent_type}"
                else:
                    new_tag = f"I-{ent_type}"
            else:
                new_tag = 'O'

            prev_type = ent_type

        iob2_sent.append({
            'token': token,
            'pos': pos,
            'label': new_tag if new_tag in VALID_BIO_TAGS else 'O'
        })

    return iob2_sent


def parse_conll_file(filepath):
    """
    Parses a CoNLL-2003 formatted file line by line into list of sentences.
    Each sentence is a list of token dicts: [{'token': ..., 'pos': ..., 'label': ...}]
    """
    if not os.path.exists(filepath):
        return [], 0

    sentences = []
    current_sent = []
    malformed_count = 0

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('-DOCSTART-'):
                if current_sent:
                    sentences.append(raw_iob1_to_iob2(current_sent))
                    current_sent = []
                continue

            parts = line.split()
            if len(parts) >= 2:
                token = parts[0]
                pos = parts[1] if len(parts) >= 4 else (parts[1] if len(parts) == 3 else 'NN')
                label = parts[-1]
                current_sent.append({
                    'token': token,
                    'pos': pos,
                    'label': label
                })
            else:
                malformed_count += 1

        if current_sent:
            sentences.append(raw_iob1_to_iob2(current_sent))

    return sentences, malformed_count


def compute_dataset_statistics():
    """
    Calculates statistics across train.txt, valid.txt, and test.txt in CoNLL dataset directory.
    Saves JSON summary to data/processed/ner/ner_stats.json.
    """
    train_path = os.path.join(RAW_NER_DIR, 'train.txt')
    valid_path = os.path.join(RAW_NER_DIR, 'valid.txt')
    test_path = os.path.join(RAW_NER_DIR, 'test.txt')

    dataset_found = os.path.exists(train_path) and os.path.exists(valid_path) and os.path.exists(test_path)

    if not dataset_found:
        stats = {
            'success': False,
            'dataset_found': False,
            'message': 'CoNLL-2003 raw files (train.txt, valid.txt, test.txt) missing in data/raw/ner/'
        }
        return stats

    train_sents, train_mal = parse_conll_file(train_path)
    valid_sents, valid_mal = parse_conll_file(valid_path)
    test_sents, test_mal = parse_conll_file(test_path)

    def analyze_split(sents):
        tokens_count = sum(len(s) for s in sents)
        label_dist = {}
        entity_counts = {'PERSON': 0, 'ORGANIZATION': 0, 'LOCATION': 0, 'MISCELLANEOUS': 0}

        for s in sents:
            for item in s:
                lbl = item['label']
                label_dist[lbl] = label_dist.get(lbl, 0) + 1
                if lbl.startswith('B-'):
                    ent_code = lbl.split('-')[1]
                    cat = TAG_TO_CATEGORY.get(ent_code, 'MISCELLANEOUS')
                    entity_counts[cat] = entity_counts.get(cat, 0) + 1

        return {
            'sentences': len(sents),
            'tokens': tokens_count,
            'total_entities': sum(entity_counts.values()),
            'entity_counts': entity_counts,
            'label_distribution': label_dist
        }

    train_stats = analyze_split(train_sents)
    valid_stats = analyze_split(valid_sents)
    test_stats = analyze_split(test_sents)

    total_entity_counts = {
        cat: train_stats['entity_counts'][cat] + valid_stats['entity_counts'][cat] + test_stats['entity_counts'][cat]
        for cat in ['PERSON', 'ORGANIZATION', 'LOCATION', 'MISCELLANEOUS']
    }

    stats = {
        'success': True,
        'dataset_found': True,
        'dataset_name': 'CoNLL-2003 English NER',
        'train_sentences': train_stats['sentences'],
        'valid_sentences': valid_stats['sentences'],
        'test_sentences': test_stats['sentences'],
        'total_sentences': train_stats['sentences'] + valid_stats['sentences'] + test_stats['sentences'],

        'train_tokens': train_stats['tokens'],
        'valid_tokens': valid_stats['tokens'],
        'test_tokens': test_stats['tokens'],
        'total_tokens': train_stats['tokens'] + valid_stats['tokens'] + test_stats['tokens'],

        'train_entities': train_stats['total_entities'],
        'valid_entities': valid_stats['total_entities'],
        'test_entities': test_stats['total_entities'],
        'total_entities': sum(total_entity_counts.values()),

        'entity_type_counts': total_entity_counts,
        'malformed_records': train_mal + valid_mal + test_mal,
        'label_distribution': train_stats['label_distribution']
    }

    os.makedirs(PROCESSED_NER_DIR, exist_ok=True)
    with open(STATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4)

    return stats


def word2features(sent, i):
    """
    Feature extractor for token i in sentence sent for CRF sequence model.
    Extracts surface features, prefix/suffix, POS tags, casing, and context windows (-1, +1).
    """
    word = sent[i]['token']
    postag = sent[i]['pos']

    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word[:2]': word[:2],
        'word[:3]': word[:3],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag,
        'postag[:2]': postag[:2],
    }
    if i > 0:
        word1 = sent[i-1]['token']
        postag1 = sent[i-1]['pos']
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1,
            '-1:postag[:2]': postag1[:2],
        })
    else:
        features['BOS'] = True

    if i < len(sent) - 1:
        word1 = sent[i+1]['token']
        postag1 = sent[i+1]['pos']
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1,
            '+1:postag[:2]': postag1[:2],
        })
    else:
        features['EOS'] = True

    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]


def sent2labels(sent):
    return [item['label'] for item in sent]


def train_crf_model():
    """
    Trains CRF sequence labeling model on CoNLL-2003 train dataset.
    Saves trained model to ner/models/crf_ner_model.pkl.
    """
    train_path = os.path.join(RAW_NER_DIR, 'train.txt')
    if not os.path.exists(train_path):
        return None, "Training file not found in data/raw/ner/train.txt"

    train_sents, _ = parse_conll_file(train_path)
    if not train_sents:
        return None, "No valid sentences parsed from train.txt"

    X_train = [sent2features(s) for s in train_sents]
    y_train = [sent2labels(s) for s in train_sents]

    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,
        c2=0.1,
        max_iterations=100,
        all_possible_transitions=True,
        verbose=False
    )
    crf.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(crf, MODEL_PATH)
    return crf, "CRF model trained and saved successfully."


_crf_model = None

def load_crf_model():
    """
    Loads pre-trained CRF model from file, or trains if missing.
    """
    global _crf_model
    if _crf_model is not None:
        return _crf_model

    if os.path.exists(MODEL_PATH):
        try:
            _crf_model = joblib.load(MODEL_PATH)
            return _crf_model
        except Exception:
            pass

    _crf_model, _ = train_crf_model()
    return _crf_model



def extract_entities(text):
    """
    Extracts named entities from raw user text using the trained CRF model
    with spaCy fallback context parsing.
    Returns structured entity records, category counts, token predictions, and highlighted HTML.
    """
    if not text or not text.strip():
        return {
            'success': False,
            'message': 'Please provide input text for entity extraction.'
        }

    nlp = get_spacy_nlp()
    doc = nlp(text)

    # Convert spaCy doc into sentence token list for CRF feature extraction
    spacy_tokens = []
    for token in doc:
        spacy_tokens.append({
            'token': token.text,
            'pos': token.tag_ if token.tag_ else token.pos_,
            'label': 'O'
        })

    crf = load_crf_model()
    bio_predictions = []

    if crf is not None and spacy_tokens:
        feats = sent2features(spacy_tokens)
        try:
            bio_predictions = crf.predict_single(feats)
        except Exception:
            bio_predictions = ['O'] * len(spacy_tokens)
    else:
        bio_predictions = ['O'] * len(spacy_tokens)

    # Also extract spaCy standard entities for hybrid resolution
    spacy_ents = {}
    for ent in doc.ents:
        cat = None
        if ent.label_ in ('PERSON', 'PER'):
            cat = 'PERSON'
        elif ent.label_ in ('ORG', 'ORGANIZATION'):
            cat = 'ORGANIZATION'
        elif ent.label_ in ('GPE', 'LOC', 'LOCATION', 'FAC'):
            cat = 'LOCATION'
        elif ent.label_ in ('NORP', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'PRODUCT'):
            cat = 'MISCELLANEOUS'

        if cat:
            spacy_ents[(ent.start_char, ent.end_char)] = (ent.text, cat)

    # Group BIO tags into entity spans
    entities = []
    current_entity = []
    current_cat = None
    current_bio = None

    tokens_output = []

    for i, token_dict in enumerate(spacy_tokens):
        token_str = token_dict['token']
        pos_str = token_dict['pos']
        bio_tag = bio_predictions[i] if i < len(bio_predictions) else 'O'

        tokens_output.append({
            'token': token_str,
            'pos': pos_str,
            'bio_tag': bio_tag
        })

        if bio_tag.startswith('B-'):
            if current_entity:
                ent_text = " ".join(current_entity)
                entities.append({
                    'text': ent_text,
                    'type': current_cat,
                    'bio_tag': current_bio
                })
                current_entity = []

            ent_code = bio_tag.split('-')[1]
            current_cat = TAG_TO_CATEGORY.get(ent_code, 'MISCELLANEOUS')
            current_bio = bio_code_to_tag(ent_code)
            current_entity.append(token_str)

        elif bio_tag.startswith('I-'):
            ent_code = bio_tag.split('-')[1]
            expected_cat = TAG_TO_CATEGORY.get(ent_code, 'MISCELLANEOUS')
            if current_entity and current_cat == expected_cat:
                current_entity.append(token_str)
            else:
                if current_entity:
                    entities.append({
                        'text': " ".join(current_entity),
                        'type': current_cat,
                        'bio_tag': current_bio
                    })
                current_cat = expected_cat
                current_bio = bio_code_to_tag(ent_code)
                current_entity = [token_str]

        else:  # 'O'
            if current_entity:
                entities.append({
                    'text': " ".join(current_entity),
                    'type': current_cat,
                    'bio_tag': current_bio
                })
                current_entity = []
                current_cat = None
                current_bio = None

    if current_entity:
        entities.append({
            'text': " ".join(current_entity),
            'type': current_cat,
            'bio_tag': current_bio
        })

    # Hybrid merge with spaCy entities if CRF missed explicit entities
    existing_texts = set(e['text'].lower() for e in entities)
    for (start_c, end_c), (sp_text, sp_cat) in spacy_ents.items():
        if sp_text.lower() not in existing_texts:
            bio_code = 'PER' if sp_cat == 'PERSON' else ('ORG' if sp_cat == 'ORGANIZATION' else ('LOC' if sp_cat == 'LOCATION' else 'MISC'))
            entities.append({
                'text': sp_text,
                'type': sp_cat,
                'bio_tag': bio_code
            })
            existing_texts.add(sp_text.lower())

    # Count entities by category
    entity_counts = {'PERSON': 0, 'ORGANIZATION': 0, 'LOCATION': 0, 'MISCELLANEOUS': 0}
    for e in entities:
        t = e['type']
        entity_counts[t] = entity_counts.get(t, 0) + 1

    # Generate visual entity highlighting in HTML
    highlighted_html = generate_highlighted_html(text, entities)

    return {
        'success': True,
        'text': text,
        'entities': entities,
        'entity_counts': entity_counts,
        'total_entities': len(entities),
        'tokens': tokens_output,
        'highlighted_html': highlighted_html
    }


def bio_code_to_tag(code):
    return code


def generate_highlighted_html(text, entities):
    """
    Wraps detected entities in text with CSS highlight badges.
    """
    if not entities:
        return f'<span class="text-white">{text}</span>'

    # Sort entities by text length descending so longer entities replace first
    sorted_ents = sorted(entities, key=lambda x: len(x['text']), reverse=True)

    result_html = text
    replaced_tokens = {}

    for i, ent in enumerate(sorted_ents):
        ent_text = ent['text']
        ent_type = ent['type']
        badge_class = get_css_badge_class(ent_type)

        placeholder = f"___ENT_{i}___"
        badge_html = f'<span class="entity-highlight {badge_class}" title="{ent_type}">{ent_text} <small class="entity-label">{ent_type}</small></span>'

        if ent_text in result_html:
            result_html = result_html.replace(ent_text, placeholder, 1)
            replaced_tokens[placeholder] = badge_html

    for placeholder, badge_html in replaced_tokens.items():
        result_html = result_html.replace(placeholder, badge_html)

    return result_html


def get_css_badge_class(ent_type):
    if ent_type == 'PERSON':
        return 'entity-person'
    elif ent_type == 'ORGANIZATION':
        return 'entity-org'
    elif ent_type == 'LOCATION':
        return 'entity-loc'
    elif ent_type == 'MISCELLANEOUS':
        return 'entity-misc'
    return 'entity-default'
