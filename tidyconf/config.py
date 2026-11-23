"""The Config class plus file merging and environment overrides."""

import copy
import difflib
import json
import os
from collections.abc import Iterable, Mapping, MutableMapping
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
                the value at route `section.key`, which must exist in the files.

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
        value = self._lookup(route)
        if value is _MISSING:
            if default is _MISSING:
                message = f"Key '{route}' not found"
                if suggestion := self._suggest(route):
                    message += f". Did you mean '{suggestion}'?"
                raise KeyNotFoundError(message)
            return default
        return copy.deepcopy(value)

    def __getitem__(self, route: str) -> Any:
        return self.get(route)

    def __contains__(self, route: object) -> bool:
        """Return whether a dotted route exists, e.g. `"database.port" in config`."""
        return isinstance(route, str) and self._lookup(route) is not _MISSING

    def _lookup(self, route: str) -> Any:
        node: Any = self._data
        for key in route.split("."):
            if not isinstance(node, Mapping) or key not in node:
                return _MISSING
            node = node[key]
        return node

    def _suggest(self, route: str) -> str | None:
        # Fix the first missing key; only suggest routes that actually exist.
        keys = route.split(".")
        node: Any = self._data
        for i, key in enumerate(keys):
            if not isinstance(node, Mapping):
                return None
            if key not in node:
                match = _closest(key, (k for k in node if isinstance(k, str)))
                if match is None:
                    return None
                candidate = ".".join([*keys[:i], match, *keys[i + 1 :]])
                return candidate if candidate in self else None
            node = node[key]
        return None  # pragma: no cover - only called for routes that don't exist

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
        segments = name[len(start) :].lower().split("__")
        raw = os.environ[name]
        # NAME_FILE=/path reads the value from a file (e.g. Docker/Kubernetes
        # secrets), unless a key ending in "_file" itself exists.
        if segments[-1].endswith("_file") and not _route_exists(data, segments):
            if name[:-5] in os.environ:
                raise ConfigError(f"{name}: set either {name[:-5]} or {name}, not both")
            segments[-1] = segments[-1].removesuffix("_file")
            raw = _read_secret(name, raw)
        _set_env_value(data, name, name[: len(start)], segments, raw)


def _route_exists(data: dict[str, Any], segments: list[str]) -> bool:
    node: Any = data
    for segment in segments:
        key = _match_key(node, segment) if isinstance(node, dict) else None
        if key is None:
            return False
        node = node[key]
    return True


def _read_secret(name: str, path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").rstrip("\r\n")
    except (OSError, UnicodeDecodeError) as err:
        raise ConfigError(f"{name}: cannot read secret file '{path}'") from err


def _set_env_value(
    data: dict[str, Any], name: str, prefix: str, segments: list[str], raw: str
) -> None:
    node = data
    for i, segment in enumerate(segments):
        if not isinstance(node, dict):
            raise ConfigError(f"{name}: '{segments[i - 1]}' is not a mapping")
        key = _match_key(node, segment)
        if key is None:
            route = ".".join(segments[: i + 1])
            message = f"{name}: '{route}' is not defined in the config files"
            match = _closest(segment, (k.lower() for k in node if isinstance(k, str)))
            if match is not None:
                fixed = [*segments[:i], match, *segments[i + 1 :]]
                message += f". Did you mean {prefix}{'__'.join(fixed).upper()}?"
            raise ConfigError(message)
        if i == len(segments) - 1:
            node[key] = _convert(name, raw, node[key])
        else:
            node = node[key]


def _match_key(node: Mapping[str, Any], segment: str) -> str | None:
    return next((k for k in node if isinstance(k, str) and k.lower() == segment), None)


def _closest(word: str, candidates: Iterable[str]) -> str | None:
    matches = difflib.get_close_matches(word, list(candidates), n=1)
    return matches[0] if matches else None


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
