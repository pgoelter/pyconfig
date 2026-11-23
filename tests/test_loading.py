import sys
from pathlib import Path
from typing import Any

import pytest

from tidyconf import Config, ConfigError, optional

RESOURCES = Path(__file__).parent / "resources"

BASE: dict[str, Any] = {
    "app": {"name": "demo", "debug": False, "owner": "Team Grün"},
    "database": {"host": "localhost", "port": 5432, "timeout": 1.5},
    "servers": ["alpha", "beta"],
}


@pytest.mark.parametrize("filename", ["base.json", "base.toml", "base.yaml"])
def test_load_each_format(filename: str) -> None:
    config = Config.load(RESOURCES / filename)

    assert config.to_dict() == BASE


def test_load_accepts_str_path() -> None:
    config = Config.load(str(RESOURCES / "base.json"))

    assert config.get("app.owner") == "Team Grün"


@pytest.mark.parametrize(
    ("source", "suffix"),
    [
        ("base.yaml", ".yml"),
        ("base.yaml", ".YAML"),
        ("base.json", ".JSON"),
        ("base.toml", ".Toml"),
    ],
)
def test_suffix_variants(tmp_path: Path, source: str, suffix: str) -> None:
    path = tmp_path / f"config{suffix}"
    path.write_bytes((RESOURCES / source).read_bytes())

    assert Config.load(path).to_dict() == BASE


def test_load_without_sources() -> None:
    assert Config.load().to_dict() == {}


def test_later_files_override_earlier() -> None:
    config = Config.load(RESOURCES / "base.json", RESOURCES / "override.yml")

    assert config.to_dict() == {
        "app": {"name": "demo", "debug": True, "owner": "Team Grün"},
        "database": {"host": "localhost", "port": 6543, "timeout": 1.5},
        "servers": ["gamma"],
    }


def test_scalar_replaces_mapping_and_vice_versa(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    first.write_text('{"a": {"x": 1}, "b": 2}', encoding="utf-8")
    second = tmp_path / "second.json"
    second.write_text('{"a": "flat", "b": {"y": 3}}', encoding="utf-8")

    assert Config.load(first, second).to_dict() == {"a": "flat", "b": {"y": 3}}


def test_reset_returns_to_loaded_state() -> None:
    config = Config.load(RESOURCES / "base.toml")
    config.set("database.port", 1)

    config.reset()

    assert config.to_dict() == BASE


def test_missing_required_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Config.load(tmp_path / "missing.json")


def test_missing_optional_file_is_skipped(tmp_path: Path) -> None:
    config = Config.load(RESOURCES / "base.json", optional(tmp_path / "local.json"))

    assert config.to_dict() == BASE


def test_existing_optional_file_is_loaded() -> None:
    config = Config.load(RESOURCES / "base.json", optional(RESOURCES / "override.yml"))

    assert config.get("database.port") == 6543


def test_optional_accepts_str_and_stores_path() -> None:
    marker = optional("settings.local.toml")

    assert marker.path == Path("settings.local.toml")


def test_unsupported_suffix_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.ini"
    path.write_text("[app]\nname = demo\n", encoding="utf-8")

    with pytest.raises(ConfigError, match=r"Unsupported config file type: '\.ini'"):
        Config.load(path)


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("broken.json", '{"app": '),
        ("broken.toml", "[app\nname = "),
        ("broken.yaml", "app: [unclosed"),
    ],
)
def test_parse_error_raises_config_error(
    tmp_path: Path, filename: str, content: str
) -> None:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigError, match="Could not parse") as exc_info:
        Config.load(path)

    assert exc_info.value.__cause__ is not None


@pytest.mark.parametrize(
    ("filename", "content", "typename"),
    [
        ("list.json", "[1, 2]", "list"),
        ("scalar.json", "42", "int"),
        ("list.yaml", "- a\n- b\n", "list"),
        ("scalar.yaml", "just a string\n", "str"),
    ],
)
def test_non_mapping_top_level_raises(
    tmp_path: Path, filename: str, content: str, typename: str
) -> None:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ConfigError, match=f"top level must be a mapping, got {typename}"
    ):
        Config.load(path)


def test_empty_yaml_is_empty_config(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")

    assert Config.load(path).to_dict() == {}


@pytest.mark.parametrize("suffix", [".json", ".toml", ".yaml"])
def test_utf8_content(tmp_path: Path, suffix: str) -> None:
    content = {
        ".json": '{"owner": "Grüße ✓"}',
        ".toml": 'owner = "Grüße ✓"\n',
        ".yaml": "owner: Grüße ✓\n",
    }[suffix]
    path = tmp_path / f"config{suffix}"
    path.write_bytes(content.encode("utf-8"))

    assert Config.load(path).get("owner") == "Grüße ✓"


def test_yaml_without_pyyaml_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "yaml", None)

    with pytest.raises(
        ConfigError, match=r"requires PyYAML: pip install tidyconf\[yaml\]"
    ):
        Config.load(RESOURCES / "base.yaml")


def test_missing_optional_yaml_skipped_without_pyyaml(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setitem(sys.modules, "yaml", None)

    config = Config.load(RESOURCES / "base.json", optional(tmp_path / "local.yml"))

    assert config.to_dict() == BASE


def test_json_and_toml_work_without_pyyaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "yaml", None)

    config = Config.load(RESOURCES / "base.json", RESOURCES / "base.toml")

    assert config.to_dict() == BASE
