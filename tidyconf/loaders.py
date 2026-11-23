"""Reading config files, with the format chosen by file suffix."""

import json
import os
import tomllib
from pathlib import Path
from typing import Any

from tidyconf.exceptions import ConfigError


def _load_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".json", ".toml", ".yaml", ".yml"):
        raise ConfigError(f"Unsupported config file type: '{path.suffix}' ({path})")

    try:
        if suffix == ".json":
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        elif suffix == ".toml":
            with path.open("rb") as file:
                data = tomllib.load(file)
        else:
            data = _load_yaml(path)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        raise ConfigError(f"Could not parse {path}: {err}") from err

    if not isinstance(data, dict):
        raise ConfigError(
            f"{path}: top level must be a mapping, got {type(data).__name__}"
        )
    return data


def _load_yaml(path: Path) -> Any:
    # Read first, so a missing optional file is skipped even without PyYAML.
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        raise ConfigError(
            "Reading YAML files requires PyYAML: pip install tidyconf[yaml]"
        ) from None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as err:
        raise ConfigError(f"Could not parse {path}: {err}") from err
    return {} if data is None else data
