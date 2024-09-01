from abc import ABC, abstractmethod
from typing import Callable, Any
from ._reader import Reader

class Traveler(ABC):
    """A Traveler is responsible for traversing a tree-like structure
    (e.g., directory or URL) and processing each item encountered.
    """
    
    def __init__(self, reader: Reader, callback: Callable[[Any], Any]):
        """
        Initialize the Traveler object.

        Args:
            reader (Reader): An object responsible for reading the contents
                of the traversed items.
            callback (Callable[[Any], Any]): A function that will be called
                on the content read from each leaf node.
        """
        self._reader = reader
        self._callback = callback

    @abstractmethod
    def traverse(self, uri: str) -> list[dict]:
        """
        Traverse the tree-like structure starting from the given URI.

        This method should be implemented by subclasses.

        Args:
            uri (str): The root URI (e.g., directory path or URL) to start traversing from.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - 'uri': The URI of the node
                - 'is_leaf': Boolean indicating if the node is a leaf
        """
        pass

    def traverse_all(self, uri: str) -> list[Any]:
        """
        Recursively traverse all nodes starting from the given URI,
        process leaf nodes, and return the results.

        Args:
            uri (str): The root URI to start traversing from.

        Returns:
            list[Any]: A list of processed results from all leaf nodes.
        """
        results = []
        nodes = self.traverse(uri)
        
        for node in nodes:
            if node['is_leaf']:
                content = self._reader.read(node['uri'])
                result = self._callback(content)
                results.append(result)
            else:
                results.extend(self.traverse_all(node['uri']))
        
        return results