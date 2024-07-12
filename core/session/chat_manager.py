
from core.talk._talker import Talker
from core.talk.talker_factory import TalkerFactory

class ChatManager:
    def __init__(self):
        self.factory = TalkerFactory()
        self.sessions = {}

    def create_chatbot(self, session_id)->Talker:
        if session_id not in self.sessions:
            self.sessions[session_id] = self.factory.get_instance("WebTalker")
            self.sessions[session_id].set_session_id(session_id)
        return self.sessions[session_id]

    def get_chatbot(self, session_id):
        return self.sessions.get(session_id)