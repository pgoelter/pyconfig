"""Exceptions raised by tidyconf."""


class ConfigError(Exception):
    """Raised for unreadable files, unsupported formats and bad env values."""


class KeyNotFoundError(ConfigError, KeyError):
    """Raised when a route does not exist in the configuration."""

    def __str__(self) -> str:
        # KeyError.__str__ would wrap the message in quotes.
        return str(self.args[0]) if self.args else ""
