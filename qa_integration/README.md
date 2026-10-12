# TRACE-X — QA Blueprint Integration Guide

## Overview
The **Question Answering (QA)** module is built as an isolated, standalone Flask Blueprint inside `qa_integration/qa_blueprint.py`.

In strict adherence to project preservation rules, **no existing files were modified**.

---

## 🔌 Optional Manual Integration Steps

To connect the new Question Answering System (`/qa`) into the existing TRACE-X Flask application, follow these optional steps:

### Option 1: Register Blueprint in `app/routes.py` (Recommended)

Add the following 2 lines to [app/routes.py](file:///Users/deepthi/Desktop/TRACE-X%20P1/app/routes.py):

1. **Import the blueprint at the top of `app/routes.py`**:
   ```python
   from qa_integration.qa_blueprint import qa_bp
   ```

2. **Register the blueprint inside `create_app()` in `app/__init__.py` or at the bottom of `app/routes.py`**:
   ```python
   app.register_blueprint(qa_bp)
   ```

---

### Option 2: Standalone Execution Helper

Alternatively, you can test the QA Blueprint independently without changing any app code by running the standalone server runner included in `qa_integration/standalone_runner.py`:

```bash
python3 -m qa_integration.standalone_runner
```
Then visit **[http://127.0.0.1:5055/qa](http://127.0.0.1:5055/qa)** in your web browser.
