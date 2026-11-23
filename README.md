[![CI](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/pgoelter/pyconfig/actions/workflows/main.yml)

# tidyconf

Simple configuration for small, self-hosted apps. Load settings from JSON, TOML or
YAML files, layer a local override file on top of the defaults, let environment
variables override single values, and read everything through dotted routes like
`config["database.port"]`. Fully typed, Python 3.11+, no dependencies (PyYAML only
if you use YAML files).

## Install

```sh
pip install tidyconf          # JSON and TOML
pip install "tidyconf[yaml]"  # plus YAML support (PyYAML)
```

## Usage

`config.toml` (defaults, committed to the repo):

```toml
debug = false

[server]
host = "127.0.0.1"
port = 8000

[database]
url = "sqlite:///app.db"
pool_size = 5

[features]
enabled = ["search"]
```

`config.local.yml` (optional, per machine, not committed):

```yaml
server:
  host: 0.0.0.0
database:
  url: postgresql://localhost/myapp
```

Environment (e.g. set by Docker or systemd):

```sh
export MYAPP_SERVER__PORT=9000
export MYAPP_DEBUG=true
```

Load and read:

```python
from tidyconf import Config, optional

config = Config.load(
    "config.toml",
    optional("config.local.yml"),  # skipped if the file does not exist
    env_prefix="MYAPP",
)

config["server.host"]  # '0.0.0.0' (from config.local.yml)
config["server.port"]  # 9000 (from env, converted to int)
config.get("debug")  # True (from env, converted to bool)
config.get("database")  # {'url': 'postgresql://localhost/myapp', 'pool_size': 5}
config.get("cache.ttl", default=60)  # 60 (missing key, default used)
config["cache.ttl"]  # raises KeyNotFoundError
```

### Sharing one config across your app

There is no global singleton. Load the config once in a module and import it
wherever you need it; Python's module cache makes it a single shared object:

```python
# myapp/settings.py
from pathlib import Path

from tidyconf import Config, optional

BASE_DIR = Path(__file__).resolve().parent

config = Config.load(
    BASE_DIR / "config.toml",
    optional(BASE_DIR / "config.local.yml"),
    env_prefix="MYAPP",
)
```

```python
# myapp/server.py
from myapp.settings import config


def run() -> None:
    serve(host=config["server.host"], port=config["server.port"])
```

Relative paths are resolved against the current working directory, so building
them from `__file__` as above keeps loading independent of where the app is started.

A runnable version of this setup, a tiny web server, lives in
[`examples/app.py`](examples/app.py): run `python examples/app.py` and try
`HELLO_SERVER__PORT=9000`.

## API

```python
from tidyconf import Config, optional, ConfigError, KeyNotFoundError
```

| API | Description |
| --- | --- |
| `Config(data=None)` | Create a config from a mapping (deep-copied). Handy in tests. |
| `Config.load(*sources, env_prefix=None)` | Load and deep-merge files in order (later wins), then apply env overrides if `env_prefix` is given. Env variables can only override keys defined in the files. |
| `optional(path)` | Mark a source file as optional: skipped if it does not exist. |
| `config.get(route, default=...)` | Value at a dotted route such as `"server.port"`. Returns a deep copy. Raises `KeyNotFoundError` if missing, unless `default` is given. |
| `config[route]` | Same as `config.get(route)` without a default. |
| `route in config` | Whether the route exists, e.g. `"database.port" in config`. Also `True` for keys set to `None`. |
| `config.set(route, value)` | Set a value, creating intermediate sections as needed. Raises `TypeError` if a part of the route is not a mapping. |
| `config.reset()` | Restore the state at construction / `load()` time. |
| `config.to_dict()` | Deep copy of all data as a plain `dict`. |

Because `get()` and `to_dict()` return copies, mutating a returned value never
changes the config; use `set()` for that.

File formats are chosen by suffix (case-insensitive): `.json`, `.toml`, `.yaml` / `.yml`.
Files are read as UTF-8 and the top level must be a mapping. An empty YAML file
counts as an empty mapping.

### Errors

| Exception | When |
| --- | --- |
| `ConfigError` | Unsupported file type, parse error, top level not a mapping, YAML file without PyYAML installed, invalid env override. |
| `KeyNotFoundError` | Route not found in `get()` / `[]`. Subclass of both `ConfigError` and `KeyError`. |
| `FileNotFoundError` | A required (non-`optional`) source file does not exist. |
| `TypeError` | `set()` would have to go through a value that is not a mapping. |

## Layering rules

- Sources are merged left to right; later sources win.
- If both sides have a mapping for the same key, they are merged recursively.
  Any other value (including lists) is replaced as a whole, not combined.
- Environment overrides are applied last, on top of the merged files.
- `reset()` returns to this fully loaded state.

## Environment variables

With `env_prefix="MYAPP"`, every environment variable starting with `MYAPP_` is an
override:

- The prefix is matched case-insensitively.
- The rest of the name is split on double underscores into a route:
  `MYAPP_DATABASE__POOL_SIZE` sets `database.pool_size`. Single underscores are part
  of the key.
- Each part matches an existing key case-insensitively.
- **The key must already exist in your config files.** Environment variables only
  override values, they never add new ones. An unknown variable such as
  `MYAPP_DATABSE__PORT` (note the typo) raises `ConfigError` at load time instead of
  being silently ignored. Give every setting a default in your config file; for
  secrets, use an empty placeholder like `password = ""`.
- Variables are applied in sorted order of their names.

Values are converted based on the type of the value that already exists at that
route:

| Existing value | Env value | Result |
| --- | --- | --- |
| `bool` | `true` / `1` / `yes` / `on`, `false` / `0` / `no` / `off` (any case) | `True` / `False` |
| `int` | `"9000"` | `9000` |
| `float` | `"0.5"` | `0.5` |
| `list` | JSON array, e.g. `'["search", "export"]'` | `["search", "export"]` |
| mapping (section) | anything | `ConfigError`: a whole section cannot be overridden |
| `str` or `None` | anything | the plain string |

A value that cannot be converted raises `ConfigError` naming the environment
variable, as does a route that runs through a non-mapping value.

### Limitations

- Keys containing `.` cannot be reached with dotted routes (no escaping).
- Keys containing `.` or `-` cannot be set from environment variables: shells and
  most tools do not allow those characters in variable names.
- An environment variable can only replace a single value, not a whole section or a
  single list element.

## Development

See [CLAUDE.md](CLAUDE.md) for setup, tests, linting and project conventions.

## License

MIT, see [LICENSE](LICENSE).
