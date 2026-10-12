import os
from app import create_app
from qa_integration.qa_blueprint import qa_bp

app = create_app()
app.register_blueprint(qa_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    print("=" * 60)
    print("  TRACE-X — Standalone QA System Server")
    print(f"  QA Module Online at: http://127.0.0.1:{port}/qa")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
