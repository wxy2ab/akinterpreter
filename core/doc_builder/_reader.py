


from abc import ABC, abstractmethod


class Reader(ABC):
    """
    Abstract base class for all readers.

    Readers are classes that read the content of a file and return text content.

    """

    @abstractmethod
    def read(self, url: str) -> str:
        """
        Read the content of a file and return it as a string.

        Args:
            path (str): The path to the file to read.
        returns:
            str: The content of the file.
        """
        pass
