import re
from chatbot.chatbot_utils import generate_session_id, get_current_timestamp, PRONOUN_MAP, extract_entities_from_text

class ConversationManager:
    """
    Manages multi-turn conversation sessions, message history, active evidence context,
    and entity reference tracking for pronoun resolution.
    """

    def __init__(self):
        self.sessions = {}

    def get_or_create_session(self, session_id=None):
        """Retrieves an existing session or creates a new one."""
        if not session_id or session_id not in self.sessions:
            session_id = session_id or generate_session_id()
            self.sessions[session_id] = {
                'session_id': session_id,
                'created_at': get_current_timestamp(),
                'updated_at': get_current_timestamp(),
                'evidence_context': "",
                'messages': [],
                'active_entities': {
                    'PERSON': [],
                    'LOCATION': [],
                    'ORGANIZATION': [],
                    'DATE_TIME': []
                },
                'last_answer': None,
                'last_entity_mentioned': None
            }
        return self.sessions[session_id]

    def update_evidence(self, session_id, evidence_text):
        """Updates active evidence context for the given session."""
        session = self.get_or_create_session(session_id)
        session['evidence_context'] = (evidence_text or "").strip()
        session['updated_at'] = get_current_timestamp()

        # Update entity memory cache from new evidence
        if session['evidence_context']:
            extracted = extract_entities_from_text(session['evidence_context'])
            for key, val in extracted.items():
                if val:
                    session['active_entities'][key] = list(set(session['active_entities'].get(key, []) + val))

        return session

    def clear_evidence(self, session_id):
        """Clears active evidence context while preserving message history."""
        session = self.get_or_create_session(session_id)
        session['evidence_context'] = ""
        session['updated_at'] = get_current_timestamp()
        return session

    def add_message(self, session_id, sender, text, metadata=None):
        """Appends a message to the conversation history."""
        session = self.get_or_create_session(session_id)
        msg_obj = {
            'id': f"msg_{len(session['messages']) + 1}",
            'sender': sender,
            'text': text,
            'timestamp': get_current_timestamp(),
            'metadata': metadata or {}
        }
        session['messages'].append(msg_obj)
        session['updated_at'] = get_current_timestamp()

        # If answer had a person/location, update last_entity_mentioned
        if metadata and metadata.get('answer'):
            ans = metadata['answer']
            qtype = metadata.get('question_type')
            if qtype in session['active_entities']:
                if ans not in session['active_entities'][qtype]:
                    session['active_entities'][qtype].insert(0, ans)
                session['last_entity_mentioned'] = ans

        return msg_obj

    def resolve_pronouns(self, session_id, question):
        """
        Resolves ambiguous pronouns in follow-up questions using session entity memory.
        Example: "Where did he go?" -> "Where did Marcus Vance go?"
        """
        session = self.get_or_create_session(session_id)
        words = question.split()
        resolved_words = []

        last_person = (session['active_entities'].get('PERSON', []) + [None])[0]
        last_loc = (session['active_entities'].get('LOCATION', []) + [None])[0]
        last_org = (session['active_entities'].get('ORGANIZATION', []) + [None])[0]

        for w in words:
            clean_w = re.sub(r'[^\w\s]', '', w).lower()
            if clean_w in ['he', 'him', 'his'] and last_person:
                # Retain punctuation
                punct = w[len(clean_w):] if w.lower() != clean_w else ""
                resolved_words.append(f"{last_person}{punct}")
            elif clean_w in ['she', 'her', 'hers'] and last_person:
                punct = w[len(clean_w):] if w.lower() != clean_w else ""
                resolved_words.append(f"{last_person}{punct}")
            elif clean_w in ['there', 'here'] and last_loc:
                punct = w[len(clean_w):] if w.lower() != clean_w else ""
                resolved_words.append(f"{last_loc}{punct}")
            elif clean_w == 'it' and (last_org or last_loc):
                target = last_org or last_loc
                punct = w[len(clean_w):] if w.lower() != clean_w else ""
                resolved_words.append(f"{target}{punct}")
            else:
                resolved_words.append(w)

        return " ".join(resolved_words)

    def get_history(self, session_id):
        """Returns message list for session."""
        session = self.get_or_create_session(session_id)
        return session['messages']

    def clear_session(self, session_id):
        """Resets the entire session including history and evidence."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        return self.get_or_create_session(session_id)
