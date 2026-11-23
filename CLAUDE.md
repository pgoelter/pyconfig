# CLAUDE.md

Small Python library: a process-wide singleton `Config` object holding a nested dict, loadable from JSON/YAML/TOML, accessed by dotted routes (`"a.b.c"`).

> **Current state (2026-11):** `main`/`modernize` HEAD (`6a68e0a`, "Add thread safety measures") does **not import**: unindented class docstring in `pyconfig/config.py:14` and `Lock` never imported. Even with both fixed, the `__new__`/`__init__` combo makes every construction raise `SingleInstanceException`. `HEAD~1` (`4da120c`) is the last green revision (11/11 tests pass). Check `git log` before assuming this still holds.

## Setup / test / build

Only Python 3.13 is installed locally (use `py -3.13`; bare `python` is the Microsoft Store stub). The pinned `requirements.txt` does **not** install on Python ≥3.12 (PyYAML 5.4.1 fails to build), so don't use it:

```sh
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install pytest pytest-cov pyyaml toml flake8
.venv/Scripts/python -m pytest -q --cov=pyconfig --cov-report=term-missing   # run from repo root
.venv/Scripts/python -m flake8 . --select=E9,F63,F7,F82                      # the CI gate
.venv/Scripts/python -m pip wheel . --no-deps -w dist                        # build (setup.py, setuptools)
```

- Tests must run from the repo root: fixtures use relative paths (`tests/resources/...`), and `import pyconfig` works only because pytest puts the root on `sys.path` (the package isn't installed).
- CI: `.github/workflows/main.yml` runs on push only, with a 3.6–3.9 matrix and `actions/*@v2` (both obsolete).

## Architecture

- `pyconfig/config.py`: `Config` holds everything. State is `defaults` (live dict) and `_defaults` (copy made at construction, used by `reset_config`).
  - Loaders `from_json_file` / `from_yml_file` (`yaml.FullLoader`) / `from_toml_file` (third-party `toml`) all call `cls(defaults=...)`.
  - `get(route)` is `reduce(operator.getitem, route.split("."))`. `set(route, value)` builds intermediate dicts with `setdefault`.
  - `get_instance()` lazily creates an empty instance.
- `pyconfig/_decorators.py`: `throws_keyError` maps `KeyError` to `EntryNotFoundException` (only on `get`).
- `pyconfig/exceptions.py`: `EntryNotFoundException`, `SingleInstanceException`.
- Runtime deps: `PyYAML`, `toml`. They are **not** declared in `setup.py` (`install_requires` is missing).
- Packaging: `setup.py` with `find_packages()` also ships the `tests` package as a top-level package in the wheel.

## Load-bearing / surprising behaviour (don't "fix" silently; these are public behaviour)

- The singleton lives in the class attribute `Config.__instance__` (dunder on both sides, so it's *not* name-mangled). Tests reset it by assigning `Config.__instance__ = None`; any refactor must keep a reset hook for tests.
- A second `Config(...)` or `from_*_file(...)` while an instance exists raises `SingleInstanceException`. You can't reload config without the manual reset.
- `reset_config()` assigns `_defaults` by reference, so after a reset, later `set()` calls mutate the "defaults" and a second reset no longer restores them.
- `get()` with no route returns the live internal dict, so callers can mutate config.
- `get()` through a non-dict (string or list) raises a raw `TypeError`, not `EntryNotFoundException`; there's no list-index support. Keys containing `.` are unreachable.
- Files are opened without `encoding=`, so on Windows (cp1252) UTF-8 configs with non-ASCII characters load as mojibake.
- A YAML/JSON/TOML file whose top level isn't a mapping gets stored as-is and breaks `set`/`get`.
- `tests/test_config_access.py::test_access_existing_singleton_instance` passes only because of test order: it references the fixture function without requesting it. `tests/test_config_modify.py` fixture keys contain typos (`databasae`, `ap-server`).
- The PyPI name `pyconfig` belongs to an unrelated project (3.4.0). Don't publish under it.

## Conventions

- Keep the public API stable (`Config`, `get`/`set`/`reset_config`/`get_instance`/`from_*_file`, the two exceptions, dotted routes) unless a change is explicitly a breaking-phase task.
- Add a failing test that pins current behaviour *before* changing it. Every bug fix gets a regression test.
- Google-style docstrings, type hints on public methods, f-strings, max line length 127 (matches CI flake8).
- Version lives in two places (`setup.py`, `pyconfig/__init__.py`). Bump both until it is single-sourced.
- `.idea/` is local IDE state. Don't commit it.
