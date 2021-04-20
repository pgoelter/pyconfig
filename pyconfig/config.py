#!/usr/bin/env python
import json
import yaml
import toml
import operator
from copy import deepcopy
from functools import reduce

from pyconfig._decorators import throws_keyError
from pyconfig.exceptions import SingleInstanceException


class Config(object):
    """Singleton Configuration object. Can hold config settings based on a json file.
    """
    __instance__ = None

    def __init__(self, defaults: dict = None, project_name: str = None):
        """Initialize a Config object which stores configuration settings as a dict attribute.

        Args:
            defaults (dict): Configuration settings
            project_name (str, optional): Project name. Defaults to None.
        """
        super().__init__()
        if defaults is None:
            defaults = {}

        self.defaults = deepcopy(defaults)
        self._defaults = deepcopy(defaults)
        self.project_name = project_name

        # Make sure only one instance of a Config object can be created.
        if Config.__instance__ is None:
            Config.__instance__ = self
        else:
            raise SingleInstanceException("You cannot create more than one instance!")

    @classmethod
    def from_json_file(cls, filename: str, project_name: str = None):
        """Create a Config instance that holds information from a json file.

        Args:
            filename (str): The filename/path of the json file.
            project_name (str, optional): Specifies a project name. Defaults to None.

        Returns:
            Config: Returns an instance of the Config class.
        """
        defaults = None

        with open(filename) as fd:
            defaults = json.load(fd)

        return cls(defaults=defaults, project_name=project_name)

    @classmethod
    def from_yml_file(cls, filename: str, project_name: str = None):
        """Create a Config instance that holds information from a yml file.

        Args:
            filename (str): The filename/path of the yml file.
            project_name (str, optional): Specifies a project name. Defaults to None.

        Returns:
            Config: Returns an instance of the Config class.
        """
        defaults = None

        with open(filename) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            defaults = yaml.load(file, Loader=yaml.FullLoader)

        return cls(defaults=defaults, project_name=project_name)

    @classmethod
    def from_toml_file(cls, filename: str, project_name: str = None):
        """Create a Config instance that holds information from a toml file.

        Args:
            filename (str): The filename/path of the toml file.
            project_name (str, optional): Specifies a project name. Defaults to None.

        Returns:
            Config: Returns an instance of the Config class.
        """
        defaults = None

        with open(filename) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            defaults = toml.load(file)

        return cls(defaults=defaults, project_name=project_name)

    @throws_keyError
    def get(self, route: str = None):
        """Get specific key from the config object.
        Nested keys can be accessed by passing a sequence of keys as follows:
            route='route.to.nested.key'

        Args:
            route (str): A single key or a sequence of keys.

        Returns:
            Any: The Value matching the key specified.
        """
        if route is None:
            return self.defaults
        keys = None

        keys = route.split(".")

        return reduce(operator.getitem, keys, self.defaults)

    def set(self, route: str, value):
        """Set a key to a value specified by parameter value. If a key is non-existent, the key will be created.

        Args:
            route (str): A single key or a sequence of keys.
            value (any): The value matching the key.
        """
        keys = route.split(".")

        dic = self.defaults
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def reset_config(self):
        """Reset Config instance to default values.
        """
        self.defaults = self._defaults

    @staticmethod
    def get_instance():
        """ Static method to fetch the current instance.
        """
        if not Config.__instance__:
            Config.__instance__ = Config()
        return Config.__instance__

    def __str__(self):
        return f"Config(project_name={self.project_name}, defaults={str(self.defaults)})"
