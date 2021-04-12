[![Pytest and Lint](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml)

# Pyconfig

Small config library to provide a singleton instance configuration object. Allows loading an existing configuration from a file (.json, other in progress).

# Functionality

## Loading Configuration

The following classmethods allow loading an existing configuration from a file:

```python
from pyconfig import Config
# The following methods return an singleton instance of type Config. After loading a config, it can be accessed by calling Config.get_instance()

# Load configuration from existing .json file
json_config = Config.from_json_file("./config.json")

# Load configuration from existing .yml file (not yet implemented!)
yml_config = Config.from_yml_file("./config.yml")

# Load configuration from existing .toml file (not yet implemented!)
toml_config = Config.from_toml_file("./config.toml")
```

## Accessing configuration

After either initializing an empty **Config** object or loading a configuration from a file it can be accessed as follows:

```python
# If no config is loaded before calling the following an empty Config object is initialized.
from pyconfig import Config

# Get an existing singleton instance.
config = Config.get_instance()

# Get a value of an existing key in the configuration object
# Returns the value stored in config.defaults['route']['to']['property']
config.get(route="route.to.property")
```

## Modifying Configuration

An existing configuration can be modified as follows:

```python
from pyconfig import Config

config = Config.get_instance()
# Assuming the following configuration exists in the Config object (initial state):
# {
#   "root": {
#       "property": None
#   }
# }

# Changes the value of existing key 'property' to 'value'
config.set(route="root.property", value="value")

# Add a new key value pair to the configuration
config.set(route="root.another_property", value="another_value")

# Now the configuration looks like the following:
# {
#   "root": {
#       "property": None
#       "another_property": "another_value"
#   }
# }

# Reset the configuration to the initial state
config.reset_config()

```

# Sample Usage

1. Create configuration file with json syntax and store it as **config.json**:

```json
{
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
```

2. Load the configuration with the Config object:

```python
import pyconfig as conf

my_config = config.from_json_file(filename='config.json', project_name='My Awesome Project)

# Get configuration
api_config = my_config.get("api")

# Or only get the base URL for a specified api
base_url = my_config.get("api.routes.base")


# You can also create new keys like this:
my_config.set("my.new.configuration", {'parameter_1': 1, 'parameter_2: 2})
my_new_config = my_config.get("my.new.configuration")


# Or like this:
my_config.set("new.config.server_address", "http://localhost:8000/")

server_address = my_config.get("new.config.server_address)


```
