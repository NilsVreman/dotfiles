# Sway Python standards

These standards apply to the maintained runtime scripts, tests, and development tooling under `sway/`.
Other dotfiles and the preserved i3/X11 references are outside their scope.
Tool configuration in `sway/pyproject.toml` and `sway/.pre-commit-config.yaml` is authoritative for enforced rules.
The development workflow lives in [DEVELOPING.md](../DEVELOPING.md).

## Runtime and layout

Keep the deployment and session entry points independently executable by system Python.
The runtime uses only the standard library and the existing external commands.
Treat this as a collection of scripts, not an installable package or a `src/` namespace.
Keep `deploy.sh` and adjacent `deployment.py` sufficient for trusted-copy verification and reversal outside the checkout.
Keep session code and resources inside the deployed configuration tree.
Do not introduce shared helpers that compromise either execution model.
Names beginning with `_` are private implementation details; the supported interfaces are the documented commands.
Avoid import-time I/O beyond deriving script-relative paths.

## Dependencies and tools

Use uv for development dependency management and command execution.
Development tools belong in dependency groups, never in runtime dependencies.
Prefer the standard library and existing tools over new dependencies.
Review and commit the generated lockfile with dependency changes.
Keep local virtual environments and generated caches out of version control.
Enable stable, project-appropriate Ruff rules without preview mode.
Use narrow, justified exceptions rather than exclusions that hide maintained code.
Intentional CLI output is not logging, and tests may use assertions.
Python embedded in external-command substitutes receives the same lint and strict typing checks as other maintained code.
Hook execution is a development convenience, not a runtime dependency.

## Typing and representation

Use Python 3.12 syntax, built-in generics, `|` unions, and `type` aliases.
Annotate runtime and test functions completely and keep strict mypy enabled across both.
Accept the least restrictive collection type the implementation needs and return precise types.
Use `Mapping` for read-only mapping access, `Collection` for membership, and `Sequence` for indexed or repeated traversal.
Use `Iterable` only when a single traversal is sufficient.
Prefer named structures when fields have different meanings.
Use `TypedDict` for existing JSON-shaped records and frozen, slotted dataclasses for internal immutable records when useful.
Validate untrusted JSON before using it.
Confine unavoidable `Any` and narrowing casts to the JSON input seam.
Retain unknown record fields without redefining existing recovery semantics.
Mark module constants with `Final` when reassignment would be a bug.

## Readability

Use descriptive PEP 8 names and predicate names for booleans.
Give public modules, classes, and functions imperative, Google-style docstrings.
Include argument, return, and exception documentation only when it adds to the type annotations.
Comments explain reasons and safety constraints rather than narrating code.
Delete commented-out code instead of keeping a second implementation.
Keep changes focused rather than rewriting unrelated code for stylistic uniformity.

## Errors and resource safety

Error messages never quote offending values, including paths, names, arguments, and raw OS or subprocess exceptions.
Use fixed, value-free refusal messages and preserve the documented error prefix and exit status.
Keep command-line usage errors distinct from runtime failures.
Retain recovery evidence when validation or cleanup fails.
Catch the narrowest exception that can be handled and choose exception chaining deliberately.
Reserve broad catches for actual application seams, not rethrow-only handlers.
Do not use assertions for runtime validation.
Use context managers for resources and `pathlib.Path` with explicit UTF-8 encoding for text files.
When pathlib would normalize exact recovery evidence, retain the exact text and explain the scoped exception.
Bound external operations and capture their failure output rather than accidentally publishing it.
Avoid mutable defaults and global mutable state.
Never log credentials, personal data, or clipboard contents.

## Tests and evidence

Use pytest through the confirmed public command seams.
Existing unittest-style tests may remain when they are useful; use pytest fixtures and parametrization where they improve clarity.
Test observable behavior and recovery outcomes, not private Python helpers.
Put shared sandbox setup in `tests/conftest.py` and reusable builders in `tests/helpers.py`.
Prefer real temporary files and private IPC sockets over mocking Python collaborators.
Substitute only external commands, with isolated homes, environments, and command logs.
Test subprocesses use the test runner's intended interpreter.
Keep tests deterministic and independent of live services, displays, clipboard contents, secrets, and private recovery data.
Tool-isolation checks run offline in disposable Git repositories using already cached locked tools.
New behavior and fixes require regression tests.
There is no coverage threshold.
Automated substitutes do not prove real Sway, systemd, portals, authentication, hardware, or trial success.

## Documentation and commits

Write one sentence per Markdown line and keep each fact in its designated document.
User-facing behavior and recovery guidance belong in `README.md`, internal design in `docs/architecture.md`, and development workflow in `DEVELOPING.md`.
Keep commits focused, with tests and documentation that pass the checks.
No commit-message format or commit-message hook is enforced.
