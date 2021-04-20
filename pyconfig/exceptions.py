class EntryNotFoundException(Exception):
    """Custom exception that is raised when a key is accessed that is not available in an existing Config instance.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SingleInstanceException(Exception):
    """Custom exception that is raised when the constructor Config() is called a second time, as the Config class
    follows the singleton pattern.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
