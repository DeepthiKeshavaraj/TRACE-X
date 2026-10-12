# TRACE-X Chatbot Blueprint Integration Guide

This package exposes the `chatbot_bp` Flask blueprint for mounting `/chatbot` routes into TRACE-X without modifying existing source files.

## Routes Provided

- `GET /chatbot/` -> Renders the interactive Chatbot UI (`chatbot.html`).
- `POST /chatbot/message` -> Processes multi-turn user questions and evidence context.
- `POST /chatbot/new` -> Resets the active session.
- `POST /chatbot/clear-evidence` -> Clears active evidence context.
- `GET /chatbot/history` -> Returns message history for a session ID.

## Independent Standalone Execution

To run the Chatbot module on an independent port (e.g., port `5057`):

```bash
PORT=5057 python3 -m chatbot_integration.standalone_runner
```

Then visit:
`http://127.0.0.1:5057/chatbot/`

## Mounting to Main Application

To register the blueprint in `app/__init__.py` or `run.py`:

```python
from chatbot_integration.chatbot_blueprint import chatbot_bp
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
```
