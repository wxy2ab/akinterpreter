


from ._reader import Reader




class TextFileReader(Reader):
    """
    Reader for text files.
    """
    
    def read(self, url: str) -> str:
        """
        Read the content of a text file and return it as a string.
        
        Args:
            url (str): The URL of the file to read.
        Returns:
            str: The content of the file.
        """
        with open(url, 'r') as file:
            return file.read()