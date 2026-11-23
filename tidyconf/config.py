"""The Config class plus file merging and environment overrides."""

import copy
import json
import os
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from tidyconf.exceptions import ConfigError, KeyNotFoundError
from tidyconf.loaders import _load_file

_MISSING: Any = object()
_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}


@dataclass(frozen=True)
class OptionalFile:
    """A config file that is skipped if it does not exist."""

    path: Path


def optional(path: str | os.PathLike[str]) -> OptionalFile:
    """Mark a config file as optional for `Config.load`.

    Args:
        path: Path to the config file.

    Returns:
        A marker that `Config.load` skips if the file is missing.
    """
    return OptionalFile(Path(path))


class Config:
    """Nested configuration values addressed by dotted routes like "db.port"."""

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        """Create a config from a mapping, which is deep-copied.

        Args:
            data: Initial values. `reset()` returns to this state.
        """
        self._initial: dict[str, Any] = copy.deepcopy(dict(data or {}))
        self._data: dict[str, Any] = copy.deepcopy(self._initial)

    @classmethod
    def load(
        cls,
        *sources: str | os.PathLike[str] | OptionalFile,
        env_prefix: str | None = None,
    ) -> Self:
        """Load and deep-merge config files, then apply environment overrides.

        Args:
            *sources: JSON, TOML or YAML files; later files override earlier ones.
                Wrap a path in `optional()` to skip it if it does not exist.
            env_prefix: If given, variables named `<PREFIX>_SECTION__KEY` override
                the value at route `section.key`.

        Returns:
            The loaded config. `reset()` returns to this state.

        Raises:
            FileNotFoundError: A required file does not exist.
            ConfigError: A file or environment variable could not be used.
        """
        data: dict[str, Any] = {}
        for source in sources:
            path = source.path if isinstance(source, OptionalFile) else source
            try:
                loaded = _load_file(path)
            except FileNotFoundError:
                if isinstance(source, OptionalFile):
                    continue
                raise
            data = _deep_merge(data, loaded)
        if env_prefix is not None:
            _apply_env(data, env_prefix)
        return cls(data)

    def get(self, route: str, default: Any = _MISSING) -> Any:
        """Return a deep copy of the value at a dotted route.

        Args:
            route: Dotted route such as "database.port".
            default: Returned instead of raising if the route does not exist.

        Raises:
            KeyNotFoundError: The route does not exist and no default was given.
        """
        node: Any = self._data
        for key in route.split("."):
            if not isinstance(node, Mapping) or key not in node:
                if default is _MISSING:
                    raise KeyNotFoundError(f"Key '{route}' not found")
                return default
            node = node[key]
        return copy.deepcopy(node)

    def __getitem__(self, route: str) -> Any:
        return self.get(route)

    def set(self, route: str, value: Any) -> None:
        """Set the value at a dotted route, creating intermediate sections.

        Raises:
            TypeError: An intermediate value exists but is not a mapping.
        """
        *parents, last = route.split(".")
        node: MutableMapping[str, Any] = self._data
        for i, key in enumerate(parents):
            child = node.setdefault(key, {})
            if not isinstance(child, MutableMapping):
                prefix = ".".join(parents[: i + 1])
                raise TypeError(f"Cannot set '{route}': '{prefix}' is not a mapping")
            node = child
        node[last] = value

    def reset(self) -> None:
        """Restore the state from construction or `load()`."""
        self._data = copy.deepcopy(self._initial)

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of all values."""
        return copy.deepcopy(self._data)

    def __repr__(self) -> str:
        return f"Config({self._data!r})"


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(result.get(key), Mapping) and isinstance(value, Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env(data: dict[str, Any], prefix: str) -> None:
    start = f"{prefix}_".lower()
    for name in sorted(os.environ):
        if not name.lower().startswith(start):
            continue
        *parents, last = name[len(start) :].split("__")
        node = data
        for segment in parents:
            child = node.setdefault(_match_key(node, segment), {})
            if not isinstance(child, dict):
                raise ConfigError(f"{name}: '{segment}' is not a mapping")
            node = child
        key = _match_key(node, last)
        node[key] = _convert(name, os.environ[name], node.get(key))


def _match_key(node: Mapping[str, Any], segment: str) -> str:
    lowered = segment.lower()
    return next(
        (k for k in node if isinstance(k, str) and k.lower() == lowered), lowered
    )


def _convert(name: str, raw: str, current: Any) -> Any:
    if isinstance(current, bool):
        if raw.lower() in _TRUE:
            return True
        if raw.lower() in _FALSE:
            return False
        raise ConfigError(f"{name}: expected a boolean, got {raw!r}")
    if isinstance(current, int | float):
        target = int if isinstance(current, int) else float
        try:
            return target(raw)
        except ValueError as err:
            message = f"{name}: expected {target.__name__}, got {raw!r}"
            raise ConfigError(message) from err
    if isinstance(current, list):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as err:
            raise ConfigError(f"{name}: expected a JSON list, got {raw!r}") from err
        if not isinstance(value, list):
            raise ConfigError(f"{name}: expected a JSON list, got {raw!r}")
        return value
    if isinstance(current, Mapping):
        raise ConfigError(f"{name}: cannot override a whole section")
    return raw
