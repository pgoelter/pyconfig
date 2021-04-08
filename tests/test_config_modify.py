from pyconfig import Config
import pytest


@pytest.fixture
def sample_config_object():
    config: Config = Config()

    config.set(route="database.connection.user", value="Testuser")
    config.set(route="databasae.connection.password", value="PASSWORD")
    config.set(route="database.connection.host", value="localhost")
    config.set(route="database.connection.port", value=1234)

    config.set(route="api-server.ssl", value=True)
    config.set(route="api-server.host", value="localhost")
    config.set(route="ap-server.port", value=4321)

    return config


@pytest.fixture(autouse=True)
def before():
    Config.__instance__ = None


def test_reset_config_to_default(sample_config_object):
    sample_config_object.reset_config()
    assert not sample_config_object.defaults


def test_change_value_of_existing_key(sample_config_object):
    """Passed key has existing entry in the config. The existing entry will be updated with the new value.
    """

    sample_config_object.set(
        route="database.connection.user", value="Another Testuser")

    assert sample_config_object.defaults["database"]["connection"]["user"] == "Another Testuser"


def test_set_value_for_non_existing_key():
    """Passed key has non entry in the config. A new entry with the passed key-value pair should get created.
    """
    config: Config = Config()

    config.set(route="database.connection.user", value="Testuser")

    assert config.defaults["database"]["connection"]["user"] == "Testuser"
