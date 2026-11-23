# CLAUDE.md

`tidyconf`: small, typed, dependency-free config library for self-hosted apps. Loads JSON/TOML/YAML
files, deep-merges them, applies env var overrides, and exposes values via dotted routes (`"a.b.c"`).

Renamed from `pyconfig` (that PyPI name is taken). 1.0 intentionally broke the old singleton API.

## Commands

Managed with [uv](https://docs.astral.sh/uv/). Run everything from the repo root.
On this machine `uv` is not on the Git Bash PATH: use
`/c/Users/pgoel/AppData/Roaming/Python/Scripts/uv.exe` (bare `python` is the Microsoft Store stub).

```sh
uv sync                                     # create/update .venv (Python from .python-version) with dev group
uv run pytest                               # with coverage, fails under 90 %
uv run ruff check . && uv run ruff format --check .
uv run mypy                                 # strict, checks tidyconf/, tests/ and examples/
uv run --isolated --python 3.11 pytest      # any CI version locally; uv downloads it if needed
uv build                                    # sdist + wheel into dist/
```

Dev tools are the `dev` dependency group, pinned in the committed `uv.lock`; after changing
dependencies run `uv lock`. All tool config lives in `pyproject.toml` (build backend: hatchling).
CI (`.github/workflows/main.yml`) runs `uv sync --locked`, ruff, mypy and pytest on Python 3.11–3.14.

## Layout

- `tidyconf/__init__.py`: public exports and `__version__` (the only place the version lives).
- `tidyconf/config.py`: `Config`, `optional()` / `OptionalFile`, private `_deep_merge` and env logic.
- `tidyconf/loaders.py`: `_load_file(path) -> dict`, format chosen by suffix.
- `tidyconf/exceptions.py`: `ConfigError`, `KeyNotFoundError(ConfigError, KeyError)`.
- `tidyconf/py.typed`: PEP 561 marker.
- `tests/`: pytest, fixture files in `tests/resources/`.
- `examples/`: runnable demo app (`app.py` + `config.toml`); type-checked by mypy, not part of the package.

Load pipeline (`Config.load`): load each file in order -> deep merge left to right (later
wins) -> env overrides (if `env_prefix`) -> `Config(merged)`, which also snapshots the
state for `reset()`.

## Design decisions

- No singleton. Apps share one config via a module (`settings.py` does `config = Config.load(...)`).
- `get()` and `to_dict()` return deep copies; `set()` stores the value as given.
- Deep merge: mappings merge recursively, everything else (lists too) is replaced.
- Env values are converted by the type of the existing value at that route (bool before
  int!); str/None -> string; sections can't be overridden.
- Env vars only override existing keys; an unknown `<PREFIX>_*` var raises `ConfigError`
  (catches typos instead of silently adding keys).
- PyYAML is an optional extra, imported lazily inside the YAML branch only.
- Missing required file raises the builtin `FileNotFoundError`; `optional()` files are skipped.
- Keys containing `.` are unreachable by design (no escaping).

## Conventions

- PEP 8 via ruff (rules E, F, I, UP, B, SIM), line length 88, ruff format.
- Type hints everywhere; `mypy --strict` must pass for code and tests.
- Short Google-style docstrings on the public API.
- KISS / YAGNI: no features beyond what's documented in README.md without a real need.
- Every bug fix gets a regression test.
- Docs live only in `README.md` (users) and this file (developers). No other markdown files.
- `.idea/` is local IDE state; never commit it.
- Git: commit regularly with the user as author; never push.
