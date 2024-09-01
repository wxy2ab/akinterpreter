import os
from typing import Callable, Any
from ._traveler import Traveler
from ._reader import Reader

class DirectoryTraveler(Traveler):
    """A Traveler implementation for traversing file system directories."""

    def __init__(self, reader: Reader, callback: Callable[[Any], Any]):
        """
        Initialize the DirectoryTraveler.

        Args:
            reader (Reader): An object responsible for reading the contents of files.
            callback (Callable[[Any], Any]): A function that will be called
                on the content read from each file.
        """
        super().__init__(reader, callback)

    def traverse(self, path: str) -> list[dict]:
        """
        Traverse the directory structure starting from the given path.

        Args:
            path (str): The root directory path to start traversing from.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - 'uri': The file or directory path
                - 'is_leaf': Boolean indicating if the path is a file (True) or directory (False)
        """
        results = []
        
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    entry_info = {
                        'uri': entry.path,
                        'is_leaf': entry.is_file()
                    }
                    results.append(entry_info)
        except PermissionError:
            print(f"Permission denied: Unable to access {path}")
        except FileNotFoundError:
            print(f"Path not found: {path}")
        except Exception as e:
            print(f"An error occurred while traversing {path}: {str(e)}")

        return results

    def traverse_all(self, path: str) -> list[Any]:
        """
        Recursively traverse all directories and files starting from the given path,
        process files, and return the results.

        Args:
            path (str): The root directory path to start traversing from.

        Returns:
            list[Any]: A list of processed results from all files.
        """
        return super().traverse_all(path)