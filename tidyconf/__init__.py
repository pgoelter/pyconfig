"""tidyconf: small, layered configuration for small apps."""

from tidyconf.config import Config, optional
from tidyconf.exceptions import ConfigError, KeyNotFoundError

__version__ = "1.0.0"

__all__ = ["Config", "ConfigError", "KeyNotFoundError", "optional"]
