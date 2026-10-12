# TRACE-X Conversational AI / Chatbot Core Module

The `chatbot` package provides evidence-grounded multi-turn conversational intelligence for TRACE-X.

## Architecture

- **`ConversationManager`** (`chatbot/conversation_manager.py`):
  - In-memory session store for tracking conversation history per session ID.
  - Active evidence context cache.
  - Named entity memory cache (`PERSON`, `LOCATION`, `ORGANIZATION`, `DATE_TIME`).
  - Contextual pronoun resolution across conversation turns (e.g., replacing *"he"*, *"she"*, *"there"* with active entities).

- **`ChatbotEngine`** (`chatbot/chatbot_engine.py`):
  - Multi-turn intent classifier (`GREETING`, `HELP`, `RESET`, `CLEAR_EVIDENCE`, `EVIDENCE_QA`).
  - Calls `qa.qa_engine.answer_question()` to extract grounded answers and supporting evidence snippets.
  - Formats responses with confidence scores, entity type badges, and evidence citations.

- **`chatbot_utils`** (`chatbot/chatbot_utils.py`):
  - Helper utilities for text sanitization, session ID generation, timestamping, and entity extraction.

## Running Tests

To run the unit tests for the Chatbot module:

```bash
python3 -m unittest chatbot/tests/test_chatbot.py
```
