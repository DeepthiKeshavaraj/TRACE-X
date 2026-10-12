import os
import json
import re
from qa.qa_engine import answer_question

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'outputs', 'qa')
REPORT_PATH = os.path.join(OUTPUT_DIR, 'qa_evaluation_report.json')

SAMPLE_EVIDENCE = (
    "John Smith, an employee of Microsoft, visited Chennai on 12 March 2026 to investigate a reported incident. "
    "He met with officer Robert Brown at the Chennai Central Railway Station headquarters at 14:00 hours. "
    "The investigation team collected network logs and evidence files from Cyberdyne Systems to analyze potential security breaches."
)

EVALUATION_DATASET = [
    {
        'id': 'test_01',
        'category': 'Location Question',
        'question': 'Where did John Smith visit?',
        'expected_answer': 'Chennai',
        'answer_present': True
    },
    {
        'id': 'test_02',
        'category': 'Date Question',
        'question': 'When did John Smith visit Chennai?',
        'expected_answer': '12 March 2026',
        'answer_present': True
    },
    {
        'id': 'test_03',
        'category': 'Organization Question',
        'question': 'Which organization employed John Smith?',
        'expected_answer': 'Microsoft',
        'answer_present': True
    },
    {
        'id': 'test_04',
        'category': 'Absent Answer Test',
        'question': 'What is the capital of France?',
        'expected_answer': 'The answer could not be found in the supplied evidence.',
        'answer_present': False
    },
    {
        'id': 'test_05',
        'category': 'Empty Evidence Test',
        'context': '',
        'question': 'Where did John Smith visit?',
        'expected_answer': 'Error',
        'answer_present': False
    },
    {
        'id': 'test_06',
        'category': 'Empty Question Test',
        'context': SAMPLE_EVIDENCE,
        'question': '',
        'expected_answer': 'Error',
        'answer_present': False
    }
]


def calculate_token_f1(predicted, ground_truth):
    """
    Calculates Token-level F1 score between predicted answer string and ground truth.
    """
    pred_tokens = re.findall(r'\b\w+\b', str(predicted).lower())
    gt_tokens = re.findall(r'\b\w+\b', str(ground_truth).lower())

    if not pred_tokens or not gt_tokens:
        return 1.0 if pred_tokens == gt_tokens else 0.0

    common = set(pred_tokens) & set(gt_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return round(f1, 4)


def calculate_exact_match(predicted, ground_truth):
    """
    Checks whether predicted answer normalized matches ground truth exactly.
    """
    p_clean = re.sub(r'\s+', ' ', str(predicted).strip().lower())
    g_clean = re.sub(r'\s+', ' ', str(ground_truth).strip().lower())
    return 1 if p_clean == g_clean else 0


def run_qa_evaluation():
    """
    Runs evaluation suite over sample evaluation dataset and returns structured performance report.
    """
    test_results = []
    exact_matches = 0
    f1_scores = []
    valid_test_count = 0

    for test_item in EVALUATION_DATASET:
        ctx = test_item.get('context', SAMPLE_EVIDENCE)
        q = test_item['question']
        gt = test_item['expected_answer']

        res = answer_question(ctx, q)
        pred = res.get('answer', '') or res.get('error_message', '')

        em = calculate_exact_match(pred, gt)
        f1 = calculate_token_f1(pred, gt)

        test_results.append({
            'id': test_item['id'],
            'category': test_item['category'],
            'question': q,
            'expected_answer': gt,
            'predicted_answer': pred,
            'exact_match': bool(em),
            'token_f1': f1,
            'confidence': res.get('confidence'),
            'status': res.get('status')
        })

        if test_item['answer_present']:
            valid_test_count += 1
            exact_matches += em
            f1_scores.append(f1)

    mean_em = round((exact_matches / valid_test_count * 100), 2) if valid_test_count > 0 else 0.0
    mean_f1 = round((sum(f1_scores) / valid_test_count * 100), 2) if valid_test_count > 0 else 0.0

    report = {
        'success': True,
        'evaluation_type': 'Sample Test Evaluation (Extractive QA Engine)',
        'total_tests': len(EVALUATION_DATASET),
        'valid_qa_tests': valid_test_count,
        'exact_match_score': mean_em,
        'mean_token_f1_score': mean_f1,
        'test_results': test_results
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)

    return report


if __name__ == '__main__':
    res = run_qa_evaluation()
    print("QA Evaluation Result:", json.dumps(res, indent=2))
