import os
from flask import Blueprint, render_template, jsonify, request
from qa.qa_engine import answer_question

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'templates')
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')

qa_bp = Blueprint(
    'qa',
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    url_prefix='/qa'
)


@qa_bp.route('/', methods=['GET'])
def qa_page():
    """
    Renders standalone Question Answering interface page.
    """
    return render_template('qa.html')


@qa_bp.route('/answer', methods=['POST'])
@qa_bp.route('/api/answer', methods=['POST'])
def api_qa_answer():
    """
    Processes evidence context and question, returning extracted answer payload.
    """
    data = request.get_json() or {}
    context = data.get('context', '')
    question = data.get('question', '')

    if not context or not context.strip():
        return jsonify({
            'success': False,
            'status': 'Error',
            'error_message': 'Please provide evidence context text.'
        })

    if not question or not question.strip():
        return jsonify({
            'success': False,
            'status': 'Error',
            'error_message': 'Please provide a question to answer.'
        })

    res = answer_question(context, question)
    return jsonify(res)
