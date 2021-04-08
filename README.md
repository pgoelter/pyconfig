[![Pytest and Lint](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml)

# pyconfig

Provides a possibility to hold project configurations. Similar to js library conf.

# Usage

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
