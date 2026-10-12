from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'trace-x-nlp-msc-secret-key-2026'

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    from chatbot_integration.chatbot_blueprint import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

    return app
