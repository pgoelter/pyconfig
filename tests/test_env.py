import re
from pathlib import Path
from typing import Any

import pytest

from tidyconf import Config, ConfigError


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.json"
    path.write_text(
        """{
          "debug": false,
          "workers": 4,
          "ratio": 0.5,
          "hosts": ["a", "b"],
          "name": "demo",
          "nothing": null,
          "Database": {"Port": 5432, "host": "localhost"}
        }""",
        encoding="utf-8",
    )
    return path


def test_prefix_and_nesting(monkeypatch: pytest.MonkeyPatch, config_file: Path) -> None:
    monkeypatch.setenv("MYAPP_DATABASE__HOST", "db.example.com")

    config = Config.load(config_file, env_prefix="MYAPP")

    assert config.get("Database.host") == "db.example.com"


def test_prefix_match_is_case_insensitive(
    monkeypatch: pytest.MonkeyPatch, config_file: Path
) -> None:
    monkeypatch.setenv("MYAPP_NAME", "from-env")

    config = Config.load(config_file, env_prefix="myapp")

    assert config.get("name") == "from-env"


def test_requires_prefix_separator(
    monkeypatch: pytest.MonkeyPatch, config_file: Path
) -> None:
    monkeypatch.setenv("MYAPPNAME", "nope")
    monkeypatch.setenv("OTHER_NAME", "nope")

    config = Config.load(config_file, env_prefix="MYAPP")

    assert config.get("name") == "demo"


def test_no_env_prefix_ignores_environment(
    monkeypatch: pytest.MonkeyPatch, config_file: Path
) -> None:
    monkeypatch.setenv("MYAPP_NAME", "from-env")

    assert Config.load(config_file).get("name") == "demo"


def test_matches_existing_keys_case_insensitively(
    monkeypatch: pytest.MonkeyPatch, config_file: Path
) -> None:
    monkeypatch.setenv("MYAPP_DATABASE__PORT", "6543")

    config = Config.load(config_file, env_prefix="MYAPP")

    assert config.get("Database") == {"Port": 6543, "host": "localhost"}


@pytest.mark.parametrize(
    ("var", "route"),
    [
        ("MYAPP_DATABSE__PORT", "databse"),  # typo in a section name
        ("MYAPP_DATABASE__USER", "database.user"),  # unknown key in a section
        ("MYAPP_BRAND_NEW", "brand_new"),
        ("MYAPP_", ""),
    ],
)
def test_unknown_key_raises(
    monkeypatch: pytest.MonkeyPatch, config_file: Path, var: str, route: str
) -> None:
    monkeypatch.setenv(var, "x")

    message = f"{var}: '{route}' is not defined in the config files"
    with pytest.raises(ConfigError, match=re.escape(message)):
        Config.load(config_file, env_prefix="MYAPP")


def test_env_without_files_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYAPP_SERVER__PORT", "8080")

    with pytest.raises(ConfigError, match="MYAPP_SERVER__PORT"):
        Config.load(env_prefix="MYAPP")


@pytest.mark.parametrize(
    ("var", "value", "route", "expected"),
    [
        ("MYAPP_DEBUG", "true", "debug", True),
        ("MYAPP_DEBUG", "YES", "debug", True),
        ("MYAPP_DEBUG", "1", "debug", True),
        ("MYAPP_DEBUG", "On", "debug", True),
        ("MYAPP_DEBUG", "False", "debug", False),
        ("MYAPP_DEBUG", "no", "debug", False),
        ("MYAPP_DEBUG", "0", "debug", False),
        ("MYAPP_DEBUG", "OFF", "debug", False),
        ("MYAPP_WORKERS", "8", "workers", 8),
        ("MYAPP_RATIO", "0.75", "ratio", 0.75),
        ("MYAPP_RATIO", "2", "ratio", 2.0),
        ("MYAPP_HOSTS", '["x", "y", "z"]', "hosts", ["x", "y", "z"]),
        ("MYAPP_HOSTS", "[]", "hosts", []),
        ("MYAPP_NAME", "123", "name", "123"),
        ("MYAPP_NOTHING", "something", "nothing", "something"),
    ],
)
def test_value_conversion(
    monkeypatch: pytest.MonkeyPatch,
    config_file: Path,
    var: str,
    value: str,
    route: str,
    expected: Any,
) -> None:
    monkeypatch.setenv(var, value)

    result = Config.load(config_file, env_prefix="MYAPP").get(route)

    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize(
    ("var", "value"),
    [
        ("MYAPP_DEBUG", "maybe"),
        ("MYAPP_WORKERS", "many"),
        ("MYAPP_WORKERS", "1.5"),
        ("MYAPP_RATIO", "half"),
        ("MYAPP_HOSTS", "a,b"),
        ("MYAPP_HOSTS", '{"a": 1}'),
        ("MYAPP_DATABASE", "postgres://localhost"),
        ("MYAPP_NAME__FIRST", "x"),
    ],
)
def test_invalid_override_raises_naming_env_var(
    monkeypatch: pytest.MonkeyPatch, config_file: Path, var: str, value: str
) -> None:
    monkeypatch.setenv(var, value)

    with pytest.raises(ConfigError, match=var):
        Config.load(config_file, env_prefix="MYAPP")


def test_env_applied_after_all_files(
    monkeypatch: pytest.MonkeyPatch, config_file: Path, tmp_path: Path
) -> None:
    later = tmp_path / "later.toml"
    later.write_text("workers = 16\n", encoding="utf-8")
    monkeypatch.setenv("MYAPP_WORKERS", "32")

    config = Config.load(config_file, later, env_prefix="MYAPP")

    assert config.get("workers") == 32


def test_reset_keeps_env_overrides(
    monkeypatch: pytest.MonkeyPatch, config_file: Path
) -> None:
    monkeypatch.setenv("MYAPP_WORKERS", "8")
    config = Config.load(config_file, env_prefix="MYAPP")
    config.set("workers", 1)

    config.reset()

    assert config.get("workers") == 8
