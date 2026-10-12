"""
TRACE-X Conversational AI / Chatbot Module
==========================================
Provides session management, multi-turn dialogue context, pronoun resolution,
and grounded evidence Question Answering powered by the spaCy / TF-IDF QA engine.
"""

from chatbot.chatbot_engine import ChatbotEngine
from chatbot.conversation_manager import ConversationManager

__all__ = ["ChatbotEngine", "ConversationManager"]
