"""
TRACE-X Chatbot Integration Package
====================================
Contains the Flask blueprint for mounting /chatbot routes and standalone execution runner.
"""

from chatbot_integration.chatbot_blueprint import chatbot_bp

__all__ = ["chatbot_bp"]
