import os
import pytest
from pyconfig import Config


@pytest.fixture(autouse=True)
def before():
    Config.__instance__ = None


def test_load_config_from_json():
    config: Config = Config.from_json_file(
        filename=f"tests{os.sep}resources{os.sep}test-config.json")

    assert config.defaults == {
        "_comment": "This file should serve as an example.",
        "api": {
            "authentification": {
                "email": "YOURMAILADDRESS",
                "password": "YOURPASSWORD",
                "ssl_certificate": "PATHTOCERT",
                "routes": {
                    "base": "BASEURL",
                    "login": "LOGINURL"
                }
            }
        }
    }


def test_load_config_from_yml():
    config: Config = Config.from_yml_file(
        filename=f"tests{os.sep}resources{os.sep}test-config.yml")

    assert config.defaults == {
        "_comment": "This file should serve as an example.",
        "api": {
            "authentification": {
                "email": "YOURMAILADDRESS",
                "password": "YOURPASSWORD",
                "ssl_certificate": "PATHTOCERT",
                "routes": {
                    "base": "BASEURL",
                    "login": "LOGINURL"
                }
            }
        }
    }


def test_load_config_from_toml():
    config: Config = Config.from_toml_file(
        filename=f"tests{os.sep}resources{os.sep}test-config.toml")

    assert config.defaults == {
        "_comment": "This file should serve as an example.",
        "api": {
            "authentification": {
                "email": "YOURMAILADDRESS",
                "password": "YOURPASSWORD",
                "ssl_certificate": "PATHTOCERT",
                "routes": {
                    "base": "BASEURL",
                    "login": "LOGINURL"
                }
            }
        }
    }
