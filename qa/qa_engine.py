import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from qa.qa_preprocessing import preprocess_context, preprocess_question, get_spacy_nlp

METHOD_NAME = "Extractive Evidence Retrieval & Entity Span Alignment (spaCy / TF-IDF)"


def find_supporting_sentence(sentences, question_info):
    """
    Ranks sentences in evidence context by cosine similarity and keyword overlap
    with the preprocessed question to find the best supporting sentence.
    """
    if not sentences:
        return None, 0.0

    clean_q = question_info['clean_question']
    keywords = question_info['keywords']

    # TF-IDF Vectorization over sentences + question
    corpus = sentences + [clean_q]
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(corpus)
        sentence_vecs = vectorizer.transform(sentences)
        q_vec = vectorizer.transform([clean_q])

        cos_sims = cosine_similarity(sentence_vecs, q_vec).flatten()
    except Exception:
        cos_sims = np.zeros(len(sentences))

    best_idx = -1
    best_score = -1.0

    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()

        # Keyword match count score
        matched_kw = sum(1 for kw in keywords if kw in sent_lower)
        kw_score = matched_kw / len(keywords) if keywords else 0.0

        # Combined score: 60% Cosine Similarity + 40% Keyword Match ratio
        combined_score = (0.6 * cos_sims[i]) + (0.4 * kw_score)

        if combined_score > best_score:
            best_score = combined_score
            best_idx = i

    if best_idx >= 0 and best_score > 0.05:
        return sentences[best_idx], round(float(best_score), 4)

    return None, 0.0


def extract_answer_span(supporting_sentence, question_info):
    """
    Extracts the precise answer span from the supporting sentence based on
    question intent type (LOCATION, DATE_TIME, PERSON, ORGANIZATION, QUANTITY, etc.) using spaCy.
    """
    if not supporting_sentence:
        return None

    nlp = get_spacy_nlp()
    doc = nlp(supporting_sentence)
    qtype = question_info['qtype']
    keywords = set(question_info['keywords'])

    # Map question types to expected spaCy entity labels
    entity_target_labels = {
        'LOCATION': {'GPE', 'LOC', 'FAC'},
        'DATE_TIME': {'DATE', 'TIME'},
        'PERSON': {'PERSON', 'PER'},
        'ORGANIZATION': {'ORG', 'ORGANIZATION'},
        'QUANTITY': {'CARDINAL', 'QUANTITY', 'MONEY', 'PERCENT'}
    }

    target_labels = entity_target_labels.get(qtype, set())

    # 1. Match named entities of expected category via spaCy doc
    if doc.ents:
        for ent in doc.ents:
            if ent.label_ in target_labels:
                if not any(kw == ent.text.lower() for kw in keywords):
                    return ent.text

    # 2. Rule/Pattern matching fallback based on question type
    if qtype == 'LOCATION':
        # Match "visited X", "to X", "in X", "at X", "near X" where X is Title Case
        loc_match = re.search(r'\b(?:visited|in|at|to|from|near)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)', supporting_sentence)
        if loc_match:
            cand = loc_match.group(1).strip()
            if cand.lower() not in keywords:
                return cand

    elif qtype == 'DATE_TIME':
        date_match = re.search(r'\b(?:\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4}|\d{1,2}:\d{2}(?:\s*hours)?)\b', supporting_sentence)
        if date_match:
            return date_match.group(0).strip()

    elif qtype == 'ORGANIZATION':
        org_match = re.search(r'\b(?:employee of|from|representatives from|at)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)', supporting_sentence)
        if org_match:
            cand = org_match.group(1).strip()
            if cand.lower() not in keywords:
                return cand

    elif qtype == 'PERSON':
        person_match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', supporting_sentence)
        if person_match:
            cand = person_match.group(1).strip()
            if cand.lower() not in keywords:
                return cand

    # 3. Fallback to noun chunks or first entity not in question
    if doc.ents:
        for ent in doc.ents:
            if not any(kw == ent.text.lower() for kw in keywords):
                return ent.text

    noun_chunks = [chunk.text for chunk in doc.noun_chunks if not any(kw == chunk.text.lower() for kw in keywords)]
    if noun_chunks:
        return noun_chunks[0]

    return supporting_sentence


def calculate_answer_confidence(sim_score, answer_span, supporting_sentence, question_info):
    """
    Calculates a dynamic relevance confidence percentage (0-100%) based on
    sentence similarity, entity match precision, and keyword overlap.
    """
    if not supporting_sentence or not answer_span:
        return 0.0

    base_score = sim_score * 100.0

    # Boost score if specific targeted entity type was matched
    nlp = get_spacy_nlp()
    doc = nlp(supporting_sentence)
    has_target_ent = any(ent.text == answer_span for ent in doc.ents)

    if has_target_ent:
        base_score += 20.0

    # Normalize to range 50% - 98%
    conf = min(98.0, max(52.0, base_score))
    return round(conf, 2)


def answer_question(context, question):
    """
    Main Question Answering Pipeline:
    1. Preprocesses context evidence and question.
    2. Identifies best supporting sentence in context.
    3. Extracts exact answer span using spaCy entity alignment.
    4. Computes confidence score and returns structured result payload.
    """
    ctx_res = preprocess_context(context)
    if not ctx_res['valid']:
        return {
            'success': False,
            'status': 'Error',
            'error_message': ctx_res['message'],
            'question': question or '',
            'answer': None,
            'supporting_evidence': None,
            'method': METHOD_NAME,
            'confidence': None
        }

    q_res = preprocess_question(question)
    if not q_res['valid']:
        return {
            'success': False,
            'status': 'Error',
            'error_message': q_res['message'],
            'question': question or '',
            'answer': None,
            'supporting_evidence': None,
            'method': METHOD_NAME,
            'confidence': None
        }

    sentences = ctx_res['sentences']
    supporting_sent, sim_score = find_supporting_sentence(sentences, q_res)

    if not supporting_sent or sim_score < 0.05:
        return {
            'success': True,
            'status': 'Answer Not Found',
            'error_message': None,
            'question': q_res['clean_question'],
            'answer': 'The answer could not be found in the supplied evidence.',
            'supporting_evidence': 'No relevant supporting sentence was identified in the evidence text.',
            'method': METHOD_NAME,
            'confidence': 0.0
        }

    answer_span = extract_answer_span(supporting_sent, q_res)
    confidence = calculate_answer_confidence(sim_score, answer_span, supporting_sent, q_res)

    return {
        'success': True,
        'status': 'Completed',
        'error_message': None,
        'question': q_res['clean_question'],
        'question_type': q_res['qtype'],
        'answer': answer_span or supporting_sent,
        'supporting_evidence': supporting_sent,
        'method': METHOD_NAME,
        'confidence': confidence,
        'context_summary': {
            'num_sentences': ctx_res['num_sentences'],
            'num_words': ctx_res['num_words']
        }
    }
