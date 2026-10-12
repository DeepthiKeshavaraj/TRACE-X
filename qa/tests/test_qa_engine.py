import unittest
from qa.qa_engine import answer_question
from qa.qa_preprocessing import preprocess_context, preprocess_question

SAMPLE_CONTEXT = (
    "John Smith, an employee of Microsoft, visited Chennai on 12 March 2026 to investigate a reported incident. "
    "He met with officer Robert Brown at the Chennai Central Railway Station headquarters at 14:00 hours."
)


class TestQAEngine(unittest.TestCase):

    def test_location_question(self):
        res = answer_question(SAMPLE_CONTEXT, "Where did John Smith visit?")
        self.assertTrue(res['success'])
        self.assertEqual(res['status'], 'Completed')
        self.assertIn('Chennai', res['answer'])
        self.assertIsNotNone(res['supporting_evidence'])

    def test_date_question(self):
        res = answer_question(SAMPLE_CONTEXT, "When did John Smith visit Chennai?")
        self.assertTrue(res['success'])
        self.assertEqual(res['status'], 'Completed')
        self.assertIn('12 March 2026', res['answer'])

    def test_organization_question(self):
        res = answer_question(SAMPLE_CONTEXT, "Which organization employed John Smith?")
        self.assertTrue(res['success'])
        self.assertEqual(res['status'], 'Completed')
        self.assertIn('Microsoft', res['answer'])

    def test_answer_not_found(self):
        res = answer_question(SAMPLE_CONTEXT, "What is the capital of France?")
        self.assertTrue(res['success'])
        self.assertEqual(res['status'], 'Answer Not Found')
        self.assertIn('could not be found', res['answer'])

    def test_empty_context(self):
        res = answer_question("", "Where did John Smith visit?")
        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 'Error')

    def test_empty_question(self):
        res = answer_question(SAMPLE_CONTEXT, "")
        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 'Error')


if __name__ == '__main__':
    unittest.main()
