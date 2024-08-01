# code_tools.py

import shelve
import os
from threading import Lock

class ShelveTools:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'shelve_tools_data')
        self.lock = Lock()

    def add_var(self, name, value):
        with self.lock:
            with shelve.open(self.db_path) as db:
                if name not in db:
                    db[name] = value
                else:
                    raise ValueError(f"Variable '{name}' already exists. Use set_var to modify it.")

    def set_var(self, name, value):
        with self.lock:
            with shelve.open(self.db_path) as db:
                db[name] = value

    def get_var(self, name):
        with self.lock:
            with shelve.open(self.db_path) as db:
                return db.get(name)

    def del_var(self, name):
        with self.lock:
            with shelve.open(self.db_path) as db:
                if name in db:
                    del db[name]
                else:
                    raise KeyError(f"Variable '{name}' does not exist.")

    def is_exists(self, name):
        with self.lock:
            with shelve.open(self.db_path) as db:
                return name in db

    def __contains__(self, name):
        return self.is_exists(name)

    def __len__(self):
        with self.lock:
            with shelve.open(self.db_path) as db:
                return len(db)

    def __iter__(self):
        with self.lock:
            with shelve.open(self.db_path) as db:
                return iter(db.keys())

    def __getitem__(self, name):
        return self.get_var(name)

    def __setitem__(self, name, value):
        with shelve.open(self.db_path) as db:
            is_in = name in db
            if is_in:
                self.set_var(name, value)
            else:
                self.add_var(name, value)


shelve_tools = ShelveTools()