import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print("=" * 60)
    print("  TRACE-X — Temporal Relationship & Evidence Correlation Intelligence System")
    print(f"  Phase I Server starting at: http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
