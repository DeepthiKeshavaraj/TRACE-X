import os
from flask import Flask
from chatbot_integration.chatbot_blueprint import chatbot_bp

app = Flask(__name__, template_folder='../app/templates', static_folder='../app/static')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

@app.route('/')
def index():
    return '<p>TRACE-X Chatbot Module is active. Visit <a href="/chatbot/">/chatbot/</a></p>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5057))
    print(f"Starting TRACE-X Standalone Chatbot Server on http://127.0.0.1:{port}/chatbot/")
    app.run(host='0.0.0.0', port=port, debug=True)
