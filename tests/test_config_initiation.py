from pyconfig import Config
import pytest


@pytest.fixture
def empty_config_object_representation():
    return "Config(project_name=None, defaults={})"


@pytest.fixture(autouse=True)
def before():
    Config.__instance__ = None


def test_create_empty_configuration_by_get_instance(empty_config_object_representation):
    raise
    assert str(Config.get_instance()) == empty_config_object_representation


def test_create_empty_configuration_by_constructor(empty_config_object_representation):
    assert str(Config()) == empty_config_object_representation
