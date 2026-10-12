import os
import json
import sklearn_crfsuite
from seqeval.metrics import classification_report as seqeval_report
from seqeval.metrics import precision_score, recall_score, f1_score, accuracy_score
from ner.ner_processing import (
    RAW_NER_DIR,
    RESULTS_DIR,
    parse_conll_file,
    sent2features,
    sent2labels,
    load_crf_model
)

EVAL_RESULTS_PATH = os.path.join(RESULTS_DIR, 'ner_metrics.json')


def evaluate_ner_model():
    """
    Runs entity-level and token-level evaluation of the trained CRF model
    on the official CoNLL-2003 English test dataset (test.txt) using seqeval.
    Saves and returns evaluation metrics.
    """
    test_path = os.path.join(RAW_NER_DIR, 'test.txt')
    if not os.path.exists(test_path):
        return {
            'success': False,
            'message': 'Test dataset file data/raw/ner/test.txt not found.'
        }

    test_sents, malformed = parse_conll_file(test_path)
    if not test_sents:
        return {
            'success': False,
            'message': 'No valid sentences parsed from test.txt.'
        }

    crf = load_crf_model()
    if crf is None:
        return {
            'success': False,
            'message': 'CRF NER model could not be loaded or trained.'
        }

    X_test = [sent2features(s) for s in test_sents]
    y_true = [sent2labels(s) for s in test_sents]
    y_pred = crf.predict(X_test)

    # Entity-level metrics via seqeval
    overall_p = round(precision_score(y_true, y_pred) * 100, 2)
    overall_r = round(recall_score(y_true, y_pred) * 100, 2)
    overall_f1 = round(f1_score(y_true, y_pred) * 100, 2)
    token_acc = round(accuracy_score(y_true, y_pred) * 100, 2)

    # Formatted seqeval string report
    report_str = seqeval_report(y_true, y_pred, digits=4)

    # Compute per-category metrics (PER, ORG, LOC, MISC)
    category_metrics = {}
    categories = ['PER', 'ORG', 'LOC', 'MISC']
    cat_names = {'PER': 'PERSON', 'ORG': 'ORGANIZATION', 'LOC': 'LOCATION', 'MISC': 'MISCELLANEOUS'}

    for cat in categories:
        cat_name = cat_names[cat]
        # Filter sequences for category specific evaluation
        cat_true = []
        cat_pred = []

        tp = 0
        fp = 0
        fn = 0

        for true_sent, pred_sent in zip(y_true, y_pred):
            for t_lbl, p_lbl in zip(true_sent, pred_sent):
                is_true_cat = (t_lbl == f"B-{cat}" or t_lbl == f"I-{cat}")
                is_pred_cat = (p_lbl == f"B-{cat}" or p_lbl == f"I-{cat}")

                if is_true_cat and is_pred_cat:
                    tp += 1
                elif not is_true_cat and is_pred_cat:
                    fp += 1
                elif is_true_cat and not is_pred_cat:
                    fn += 1

        p = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
        r = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
        f = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
        sup = tp + fn

        category_metrics[cat_name] = {
            'precision': round(p, 2),
            'recall': round(r, 2),
            'f1_score': round(f, 2),
            'support': sup
        }

    results = {
        'success': True,
        'model_type': 'Conditional Random Fields (CRF) - Sequence Labeling',
        'dataset_evaluated': 'CoNLL-2003 English Test Set',
        'sentences_evaluated': len(test_sents),
        'token_accuracy': token_acc,
        'overall_precision': overall_p,
        'overall_recall': overall_r,
        'overall_f1': overall_f1,
        'category_metrics': category_metrics,
        'classification_report_str': report_str
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(EVAL_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    return results


def get_saved_ner_metrics():
    """
    Returns saved NER metrics from JSON, or runs evaluation if not yet computed.
    """
    if os.path.exists(EVAL_RESULTS_PATH):
        try:
            with open(EVAL_RESULTS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return evaluate_ner_model()
