from typing import Any

import pytest

from tidyconf import Config, ConfigError, KeyNotFoundError


@pytest.fixture
def config() -> Config:
    return Config(
        {
            "app": {"name": "demo", "debug": False},
            "database": {"host": "localhost", "port": 5432},
            "servers": ["alpha", "beta"],
        }
    )


def test_empty_config() -> None:
    assert Config().to_dict() == {}


def test_constructor_copies_input() -> None:
    data: dict[str, Any] = {"database": {"port": 5432}}
    config = Config(data)

    data["database"]["port"] = 1

    assert config.get("database.port") == 5432


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        ("app.name", "demo"),
        ("app.debug", False),
        ("database.port", 5432),
        ("servers", ["alpha", "beta"]),
        ("app", {"name": "demo", "debug": False}),
    ],
)
def test_get(config: Config, route: str, expected: Any) -> None:
    assert config.get(route) == expected


def test_getitem(config: Config) -> None:
    assert config["database.host"] == "localhost"


@pytest.mark.parametrize("route", ["missing", "app.missing", "app.name.deeper"])
def test_get_missing_raises(config: Config, route: str) -> None:
    with pytest.raises(KeyNotFoundError) as exc_info:
        config.get(route)

    assert str(exc_info.value) == f"Key '{route}' not found"


def test_getitem_missing_raises(config: Config) -> None:
    with pytest.raises(KeyNotFoundError, match="Key 'app.missing' not found"):
        config["app.missing"]


def test_key_not_found_error_hierarchy(config: Config) -> None:
    with pytest.raises(KeyError):
        config.get("missing")
    with pytest.raises(ConfigError):
        config.get("missing")


@pytest.mark.parametrize("default", [None, 0, "fallback", False])
def test_get_missing_returns_default(config: Config, default: Any) -> None:
    assert config.get("app.missing", default) == default


def test_get_existing_ignores_default(config: Config) -> None:
    assert config.get("app.name", "fallback") == "demo"


def test_get_returns_copy(config: Config) -> None:
    config.get("servers").append("gamma")
    config.get("app")["name"] = "changed"

    assert config.get("servers") == ["alpha", "beta"]
    assert config.get("app.name") == "demo"


def test_set_existing_key(config: Config) -> None:
    config.set("database.port", 6543)

    assert config.get("database.port") == 6543
    assert config.get("database.host") == "localhost"


def test_set_creates_intermediate_dicts(config: Config) -> None:
    config.set("cache.redis.url", "redis://localhost")

    assert config.get("cache") == {"redis": {"url": "redis://localhost"}}


def test_set_top_level_key() -> None:
    config = Config()

    config.set("name", "demo")

    assert config.to_dict() == {"name": "demo"}


def test_set_through_non_mapping_raises(config: Config) -> None:
    with pytest.raises(
        TypeError, match="Cannot set 'app.name.first': 'app.name' is not a mapping"
    ):
        config.set("app.name.first", "x")


def test_reset_restores_initial_state(config: Config) -> None:
    config.set("database.port", 1)
    config.set("new.key", "value")

    config.reset()

    assert config.get("database.port") == 5432
    assert config.get("new", None) is None


def test_reset_is_repeatable(config: Config) -> None:
    config.set("app.name", "first")
    config.reset()
    config.set("app.name", "second")
    config.reset()

    assert config.get("app.name") == "demo"


def test_to_dict(config: Config) -> None:
    assert config.to_dict() == {
        "app": {"name": "demo", "debug": False},
        "database": {"host": "localhost", "port": 5432},
        "servers": ["alpha", "beta"],
    }


def test_to_dict_returns_copy(config: Config) -> None:
    data = config.to_dict()
    data["app"]["name"] = "changed"
    data["servers"].append("gamma")

    assert config.get("app.name") == "demo"
    assert config.get("servers") == ["alpha", "beta"]


def test_repr() -> None:
    assert repr(Config({"a": {"b": 1}})) == "Config({'a': {'b': 1}})"
