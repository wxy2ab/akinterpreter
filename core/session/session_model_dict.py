

from collections import UserDict
from .session_model import SessionModel


class SessionModelDict(UserDict):
    def __init__(self, initial_dict=None):
        super().__init__()
        if initial_dict:
            for value in initial_dict.values():
                self.add(value)

    def __setitem__(self, key, value):
        if not isinstance(value, SessionModel):
            raise ValueError("Value must be an instance of SessionModel")
        super().__setitem__(value.session_id, value)

    def add(self, session_model: SessionModel):
        self[session_model.session_id] = session_model