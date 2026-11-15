# Developing the Sway scripts

Development uses a locked, non-package uv project; no project installation is needed.
Read [the standards](docs/coding-standards.md) before editing, [the architecture](docs/architecture.md) for implementation details, and [the README](README.md) for the runtime and recovery interface.
Live operations require their own authorization; editing a deployed symlink target can change a live session.

## Local checks

Run the following commands from `sway/` to synchronize the development environment and check all maintained Python, including test substitutes.
Ruff receives explicit maintained paths so it never formats the private recovery area or i3/X11 references.

```sh
uv sync --locked
uv run --locked ruff check deployment.py configuration/scripts tests
uv run --locked ruff format --check deployment.py configuration/scripts tests
uv run --locked mypy
```

Use `ruff check --fix` or omit the formatter's `--check` only when you intend to change those files.
Run an individual test file regularly while changing its command interface; the full-suite command is in [Isolated checks](README.md#isolated-checks).

```sh
uv run --locked pytest tests/test_session.py
```

## Interpreter matrix

Use a separate environment for each interpreter so neither run silently changes the other's environment.
The tests pass their interpreter through to deployment commands, session commands, guards, and external-command substitutes.

```sh
UV_PROJECT_ENVIRONMENT=.venv-py312 uv run --locked --python 3.12 pytest tests
UV_PROJECT_ENVIRONMENT=.venv-system uv run --locked --python /usr/bin/python3 pytest tests
```

These commands also exercise the configured hooks in disposable Git repositories, offline against the tools cached by the outer uv run.
They do not require or install hooks in the working repository.
Use the actual system Python path when it differs from the example.

## Optional pre-commit use

Hook installation is opt-in and is never part of the tests or implementation workflow in the working repository.
If you choose to install it yourself, run this command from the repository root so the hook records the nested configuration path.

```sh
uv run --project sway --locked pre-commit install --config sway/.pre-commit-config.yaml --hook-type pre-commit
```

Normal commits then run Ruff fixes and formatting only on staged, maintained Sway Python files.
Pre-commit temporarily stashes unstaged tracked changes; on a conflict it restores them and rolls back hook fixes rather than discarding user work.
Project-wide mypy is non-mutating and also runs for changes to the Sway project configuration, hook configuration, or lockfile.
All hooks select the nested locked uv project even though Git invokes them from the repository root.
No pytest or commit-message hook is configured.
For an explicit non-commit run on staged files, use the same nested path.

```sh
uv run --project sway --locked pre-commit run --config sway/.pre-commit-config.yaml
```

An explicit `--all-files` run chooses all matching tracked Sway files rather than only staged ones.
Use it only when that wider formatting scope is intended.
