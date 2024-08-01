# code_tools.py

from threading import Lock

class CodeTools:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CodeTools, cls).__new__(cls)
                cls._instance.data = {}
        return cls._instance

    def add_var(self, name, value):
        with self._lock:
            if name not in self.data:
                self.data[name] = value
            else:
                raise ValueError(f"Variable '{name}' already exists. Use set_var to modify it.")

    def set_var(self, name, value):
        with self._lock:
            self.data[name] = value

    def get_var(self, name):
        with self._lock:
            return self.data.get(name)

    def del_var(self, name):
        with self._lock:
            if name in self.data:
                del self.data[name]
            else:
                raise KeyError(f"Variable '{name}' does not exist.")

    def clear(self):
        with self._lock:
            self.data.clear()

tools = CodeTools()