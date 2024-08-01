# code_tools.py

from threading import Lock
from ..interpreter.data_summarizer import DataSummarizer

class CodeTools:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CodeTools, cls).__new__(cls)
                cls._instance.data = {}
                cls._instance.summarizer = DataSummarizer()
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
                summary_name = f"{name}_summary"
                if summary_name in self.data:
                    del self.data[summary_name]
            else:
                raise KeyError(f"Variable '{name}' does not exist.")

    def clear(self):
        with self._lock:
            self.data.clear()

    def add(self, name, value):
        with self._lock:
            if name not in self.data:
                self.data[name] = value
                # Check if value is NOT one of the excluded types
                if not isinstance(value, (str, int, float, bool, complex)):
                    summary = self.summarizer.get_data_summary(value)
                    self.data[f"{name}_summary"] = summary

            else:
                raise ValueError(f"Variable '{name}' already exists. Use set_var to modify it.")

    def is_exists(self, name):
        with self._lock:
            return name in self.data

    def __contains__(self, name):
        return self.is_exists(name)

    def __iter__(self):
        with self._lock:
            return iter(self.data)

    def __getitem__(self, name):
        with self._lock:
            if name in self.data:
                return self.data[name]
            else:
                raise KeyError(f"Variable '{name}' does not exist.")

    def __setitem__(self, name, value):
        if name in self.data:
            self.set_var(name, value)
        else:
            self.add_var(name, value)

    def __len__(self):
        with self._lock:
            return len(self.data)
        
code_tools = CodeTools()