from abc import ABC, abstractmethod


class FileReader(ABC):
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = None
        self.summary = ""

    @abstractmethod
    def read_file(self):
        pass

    def get_content(self):
        return self.content

    def get_summary(self):
        return self.summary