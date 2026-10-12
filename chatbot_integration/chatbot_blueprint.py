from flask import Blueprint, render_template, request, jsonify
from chatbot.chatbot_engine import ChatbotEngine
from chatbot.conversation_manager import ConversationManager

chatbot_bp = Blueprint('chatbot', __name__, template_folder='../app/templates')

# Shared engine instance for blueprint execution
conv_manager = ConversationManager()
engine = ChatbotEngine(conversation_manager=conv_manager)

@chatbot_bp.route('/', methods=['GET'])
def chatbot_index():
    """Renders the main Chatbot interface page."""
    return render_template('chatbot.html')

@chatbot_bp.route('/message', methods=['POST'])
def handle_message():
    """Processes user chat messages and returns grounded bot responses."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    user_msg = data.get('message', '').strip()
    evidence = data.get('evidence')

    if not user_msg:
        return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

    bot_msg = engine.process_message(session_id, user_msg, evidence_text=evidence)
    return jsonify({
        'success': True,
        'message': bot_msg
    })

@chatbot_bp.route('/new', methods=['POST'])
def reset_session():
    """Resets conversation session history."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    conv_manager.clear_session(session_id)
    return jsonify({'success': True, 'status': 'Session reset successfully.'})

@chatbot_bp.route('/clear-evidence', methods=['POST'])
def clear_evidence():
    """Clears evidence context from active session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    conv_manager.clear_evidence(session_id)
    return jsonify({'success': True, 'status': 'Evidence context cleared.'})

@chatbot_bp.route('/history', methods=['GET'])
def get_history():
    """Retrieves session message history."""
    session_id = request.args.get('session_id')
    history = conv_manager.get_history(session_id)
    return jsonify({'success': True, 'history': history})
