import os
from flask import Blueprint, render_template, jsonify, request
from preprocessing.data_preprocessing import (
    check_raw_files_status,
    validate_raw_datasets,
    run_preprocessing_pipeline,
    PROCESSED_FILE_PATH
)
from eda.exploratory_analysis import get_eda_summary
from classification.text_classification import (
    train_and_evaluate_models,
    predict_custom_text,
    get_saved_model_metrics,
    RESULTS_CSV_PATH,
    BEST_MODEL_PATH
)
from speech.speech_processing import process_audio_transcription
from multilingual.multilingual_processing import (
    detect_and_process_multilingual_text,
    translate_multilingual_text
)
from ner.ner_processing import (
    extract_entities,
    compute_dataset_statistics
)
from ner.ner_evaluation import get_saved_ner_metrics
from qa.qa_engine import answer_question

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/scope')
def scope():
    return render_template('scope.html')

@main_bp.route('/data')
def data():
    return render_template('data.html')

@main_bp.route('/classification')
def classification():
    return render_template('classification.html')

@main_bp.route('/speech')
def speech():
    return render_template('speech.html')

@main_bp.route('/multilingual')
def multilingual():
    return render_template('multilingual.html')

@main_bp.route('/ner')
def ner():
    return render_template('ner.html')

@main_bp.route('/qa')
def qa():
    return render_template('qa.html')

@main_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# ==================== API ENDPOINTS ====================

@main_bp.route('/api/dashboard-summary', methods=['GET'])
def api_dashboard_summary():
    """
    Returns dynamic dashboard KPI values computed from actual datasets/model results.
    """
    data_status = check_raw_files_status()
    processed_exists = os.path.exists(PROCESSED_FILE_PATH)
    eda = get_eda_summary() if processed_exists else {}
    
    models_trained = os.path.exists(BEST_MODEL_PATH) and os.path.exists(RESULTS_CSV_PATH)
    
    total_records = eda.get('total_records', data_status.get('total_raw_records', 0))
    total_categories = eda.get('total_categories', len(data_status.get('categories_found', [])))
    
    best_accuracy = "N/A"
    best_f1 = "N/A"
    train_records = 0
    test_records = 0
    
    if models_trained:
        saved_metrics = get_saved_model_metrics()
        if saved_metrics:
            best_acc_val = max(m.get('Accuracy', 0) for m in saved_metrics)
            best_f1_val = max(m.get('F1 Score', 0) for m in saved_metrics)
            best_accuracy = f"{best_acc_val}%"
            best_f1 = f"{best_f1_val}%"
            
            if total_records > 0:
                train_records = int(total_records * 0.8)
                test_records = total_records - train_records

    progress_checklist = {
        'scope_defined': True,
        'data_collected': data_status.get('found_count', 0) > 0,
        'data_preprocessed': processed_exists,
        'classification_implemented': models_trained,
        'speech_processing_implemented': True,
        'multilingual_nlp_implemented': True,
        'ner_implemented': True,
        'qa_implemented': True
    }
    
    completed_steps = sum(1 for v in progress_checklist.values() if v)
    current_status = "Completed" if completed_steps == len(progress_checklist) else "In Progress"

    return jsonify({
        'total_records': total_records,
        'categories_count': total_categories,
        'train_records': train_records,
        'test_records': test_records,
        'best_model_accuracy': best_accuracy,
        'best_model_f1': best_f1,
        'progress_checklist': progress_checklist,
        'current_status': current_status,
        'completed_steps': completed_steps,
        'total_steps': len(progress_checklist),
        'dataset_found': data_status.get('found_count', 0) > 0
    })

@main_bp.route('/api/data-status', methods=['GET'])
def api_data_status():
    status = check_raw_files_status()
    return jsonify(status)

@main_bp.route('/api/run-validation', methods=['POST'])
def api_run_validation():
    validation_res = validate_raw_datasets()
    return jsonify(validation_res)

@main_bp.route('/api/run-preprocessing', methods=['POST'])
def api_run_preprocessing():
    res = run_preprocessing_pipeline()
    return jsonify(res)

@main_bp.route('/api/eda-stats', methods=['GET'])
def api_eda_stats():
    eda_res = get_eda_summary()
    return jsonify(eda_res)

@main_bp.route('/api/train-models', methods=['POST'])
def api_train_models():
    res = train_and_evaluate_models()
    return jsonify(res)

@main_bp.route('/api/model-results', methods=['GET'])
def api_model_results():
    if not os.path.exists(BEST_MODEL_PATH):
        if os.path.exists(PROCESSED_FILE_PATH):
            train_res = train_and_evaluate_models()
            return jsonify(train_res)
        else:
            return jsonify({
                'success': False,
                'message': 'Processed dataset not found. Please run preprocessing first.'
            })
    
    res = train_and_evaluate_models()
    return jsonify(res)

@main_bp.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json() or {}
    text = data.get('text', '')
    model_name = data.get('model', None)
    
    if not text:
        return jsonify({'success': False, 'message': 'Please provide text for classification.'})
        
    res = predict_custom_text(text, model_name)
    return jsonify(res)

# ==================== SPEECH PROCESSING API ====================

@main_bp.route('/api/speech/transcribe', methods=['POST'])
def api_speech_transcribe():
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file uploaded.'})
        
    audio_file = request.files['audio']
    reference_text = request.form.get('reference_text', None)
    live_transcript = request.form.get('live_transcript', None)
    
    res = process_audio_transcription(audio_file, reference_text, live_transcript)
    return jsonify(res)

# ==================== MULTILINGUAL NLP API ====================

@main_bp.route('/api/multilingual/process', methods=['POST'])
def api_multilingual_process():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text or not text.strip():
        return jsonify({'success': False, 'message': 'Please provide text for multilingual analysis.'})
        
    res = detect_and_process_multilingual_text(text)
    return jsonify(res)

@main_bp.route('/api/multilingual/translate', methods=['POST'])
def api_multilingual_translate():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text or not text.strip():
        return jsonify({'success': False, 'message': 'Please provide text for translation.'})
        
    res = translate_multilingual_text(text)
    return jsonify(res)

# ==================== NAMED ENTITY RECOGNITION (NER) API ====================

@main_bp.route('/api/ner/process', methods=['POST'])
def api_ner_process():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text or not text.strip():
        return jsonify({'success': False, 'message': 'Please provide text for entity analysis.'})
        
    res = extract_entities(text)
    return jsonify(res)

@main_bp.route('/api/ner/stats', methods=['GET'])
def api_ner_stats():
    dataset_stats = compute_dataset_statistics()
    eval_metrics = get_saved_ner_metrics()
    return jsonify({
        'success': True,
        'dataset_stats': dataset_stats,
        'eval_metrics': eval_metrics
    })

# ==================== QUESTION ANSWERING (QA) API ====================

@main_bp.route('/qa/answer', methods=['POST'])
@main_bp.route('/api/qa/answer', methods=['POST'])
def api_qa_answer():
    data = request.get_json() or {}
    context = data.get('context', '')
    question = data.get('question', '')
    
    if not context or not context.strip():
        return jsonify({'success': False, 'status': 'Error', 'error_message': 'Please provide evidence context text.'})
        
    if not question or not question.strip():
        return jsonify({'success': False, 'status': 'Error', 'error_message': 'Please provide a question to answer.'})
        
    res = answer_question(context, question)
    return jsonify(res)

# ==================== UNIFIED DOCUMENT & IMAGE TEXT EXTRACTION API ====================

@main_bp.route('/api/extract-text', methods=['POST'])
def api_extract_text():
    """
    Extracts text from uploaded documents (.txt, .pdf, .docx) and images (.png, .jpg, .jpeg, .webp, .bmp, .tif, .tiff).
    Supports multiple files with automatic text concatenation.
    """
    uploaded_files = request.files.getlist('files') or request.files.getlist('file')

    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({
            'success': False,
            'extracted_text': '',
            'filenames': [],
            'error': 'No file was uploaded. Please select one or more files.'
        }), 400

    from preprocessing.document_extraction import extract_text_from_multiple_files
    res = extract_text_from_multiple_files(uploaded_files)

    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

