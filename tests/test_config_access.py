from pyconfig import Config
import pytest


@pytest.fixture
def sample_config_object():
    Config.__instance__ = None
    config: Config = Config()

    config.set(route="database.connection.user", value="Testuser")
    config.set(route="database.connection.password", value="PASSWORD")
    config.set(route="database.connection.host", value="localhost")
    config.set(route="database.connection.port", value=1234)

    config.set(route="api-server.ssl", value=True)
    config.set(route="api-server.host", value="localhost")
    config.set(route="api-server.port", value=4321)

    return config


def test_get_existing_configuration_single_value(sample_config_object):

    single_value = sample_config_object.get("database.connection.host")

    assert single_value == "localhost"


def test_get_existing_configuration_multiple_values(sample_config_object):

    multiple_values = sample_config_object.get("database.connection")

    assert multiple_values == {
        "host": "localhost",
        "port": 1234,
        "password": "PASSWORD",
        "host": "localhost",
        "user": "Testuser"}


def test_access_existing_singleton_instance():
    _not_used = sample_config_object

    singleton_instance = Config.get_instance()

    assert singleton_instance.defaults == {
        "api-server": {
            "ssl": True,
            "host": "localhost",
            "port": 4321},
        "database": {
            "connection": {
                "host": "localhost",
                "port": 1234,
                "password": "PASSWORD",
                "host": "localhost",
                "user": "Testuser"}
        }
    }
