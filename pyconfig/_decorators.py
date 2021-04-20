from functools import wraps

from pyconfig.exceptions import EntryNotFoundException


def throws_keyError(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """A wrapper function"""

        try:
            return func(*args, **kwargs)
        except KeyError as e:
            raise EntryNotFoundException(f"Key '{e.args[0]}' not found!")

    return wrapper
