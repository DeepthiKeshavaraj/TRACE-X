import unittest
from chatbot.conversation_manager import ConversationManager
from chatbot.chatbot_engine import ChatbotEngine

SAMPLE_EVIDENCE = (
    "On 12 October 2024, subject Marcus Vance was observed entering the Secure Communications Building in Sydney. "
    "He met with Dr. Elena Rostova to deliver encrypted flash drives. Later, Elena Rostova traveled to Melbourne."
)

class TestChatbotModule(unittest.TestCase):

    def setUp(self):
        self.conv_mgr = ConversationManager()
        self.engine = ChatbotEngine(conversation_manager=self.conv_mgr)
        self.session_id = "test_session_123"

    def test_greeting_intent(self):
        res = self.engine.process_message(self.session_id, "Hello")
        self.assertIn("TRACE-X Conversational AI", res['text'])
        self.assertEqual(res['sender'], 'bot')
        self.assertEqual(res['metadata']['intent'], 'GREETING')

    def test_help_intent(self):
        res = self.engine.process_message(self.session_id, "Help me with commands")
        self.assertIn("Instructions", res['text'])
        self.assertEqual(res['metadata']['intent'], 'HELP')

    def test_no_evidence_warning(self):
        res = self.engine.process_message(self.session_id, "Who visited Sydney?")
        self.assertIn("No Active Evidence Context", res['text'])

    def test_evidence_qa(self):
        res = self.engine.process_message(
            self.session_id,
            "Who visited Sydney?",
            evidence_text=SAMPLE_EVIDENCE
        )
        self.assertTrue(res['metadata']['success'])
        self.assertIn("Marcus Vance", res['text'])
        self.assertGreater(res['metadata']['confidence'], 50.0)

    def test_multi_turn_pronoun_resolution(self):
        # 1st query establishing Marcus Vance
        self.engine.process_message(
            self.session_id,
            "Who visited Sydney?",
            evidence_text=SAMPLE_EVIDENCE
        )
        # 2nd query using pronoun "he"
        res2 = self.engine.process_message(self.session_id, "Where did he go?")
        self.assertIsNotNone(res2['text'])
        self.assertIn("bot", res2['sender'])

    def test_clear_evidence(self):
        self.engine.process_message(self.session_id, "Hi", evidence_text=SAMPLE_EVIDENCE)
        self.conv_mgr.clear_evidence(self.session_id)
        session = self.conv_mgr.get_or_create_session(self.session_id)
        self.assertEqual(session['evidence_context'], "")

    def test_reset_session(self):
        self.engine.process_message(self.session_id, "Hi", evidence_text=SAMPLE_EVIDENCE)
        self.conv_mgr.clear_session(self.session_id)
        session = self.conv_mgr.get_or_create_session(self.session_id)
        self.assertEqual(len(session['messages']), 0)

if __name__ == '__main__':
    unittest.main()
