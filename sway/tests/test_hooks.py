"""Run the real hook interface only in disposable Git repositories."""

import sys

import pytest
from helpers import HookRepository


def test_automatic_fixes_touch_only_staged_sway_python(hooks: HookRepository) -> None:
    staged = hooks.root / "sway/tests/staged.py"
    staged.write_text("import os\n\nVALUE=1\n" + "# stable context\n" * 20, encoding="utf-8")
    outside = hooks.root / "outside.py"
    outside.write_text("import os\nVALUE=9\n", encoding="utf-8")
    hooks.git("add", "sway/tests/staged.py", "outside.py")
    staged.write_text(staged.read_text(encoding="utf-8") + "# unstaged sentinel\n", encoding="utf-8")
    unstaged = hooks.root / "sway/tests/unstaged.py"
    unstaged.write_text("VALUE=2\n", encoding="utf-8")
    untracked = hooks.root / "sway/tests/untracked.py"
    untracked.write_text("VALUE=3\n", encoding="utf-8")
    preserved = {path: path.read_bytes() for path in (outside, unstaged, untracked)}
    result = hooks.hooks(ok=False)
    assert "ruff-check" in result.stdout and "ruff-format" in result.stdout
    assert "mypy" in result.stdout
    text = staged.read_text(encoding="utf-8")
    assert "import os" not in text
    assert "VALUE = 1" in text
    assert text.endswith("# unstaged sentinel\n")
    for path, data in preserved.items():
        assert path.read_bytes() == data
    assert hooks.git("diff", "--cached", "--", "outside.py").stdout.endswith("+import os\n+VALUE=9\n")


@pytest.mark.parametrize("filename", ["pyproject.toml", "uv.lock", ".pre-commit-config.yaml"])
def test_configuration_only_changes_run_nonmutating_project_type_checks(hooks: HookRepository, filename: str) -> None:
    path = hooks.root / "sway" / filename
    path.write_text(path.read_text(encoding="utf-8") + "\n# configuration-only change\n", encoding="utf-8")
    hooks.git("add", str(path.relative_to(hooks.root)))
    before = hooks.contents()
    result = hooks.hooks()
    assert "mypy" in result.stdout
    assert "Passed" in next(line for line in result.stdout.splitlines() if line.startswith("mypy"))
    assert hooks.contents() == before


def test_type_checks_use_the_nested_configuration_on_config_only_changes(hooks: HookRepository) -> None:
    path = hooks.root / "sway/pyproject.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("strict = true", "strict = true\ndisallow_any_explicit = true"),
        encoding="utf-8",
    )
    hooks.git("add", "sway/pyproject.toml")
    before = hooks.contents()
    result = hooks.hooks(ok=False)
    assert "Failed" in next(line for line in result.stdout.splitlines() if line.startswith("mypy"))
    assert "explicit-any" in result.stdout
    assert hooks.contents() == before


def test_changes_outside_sway_do_not_run_tools_or_rewrite_files(hooks: HookRepository) -> None:
    (hooks.root / "outside.py").write_text("import os\nVALUE=9\n", encoding="utf-8")
    hooks.git("add", "outside.py")
    before = hooks.contents()
    result = hooks.hooks()
    assert result.stdout.count("Skipped") == 3
    assert not (hooks.root / "sway/.venv").exists()
    assert hooks.contents() == before


def test_nested_installation_selects_only_pre_commit_not_commit_message_or_tests(hooks: HookRepository) -> None:
    hooks.run([sys.executable, "-m", "pre_commit", "install", "--config", "sway/.pre-commit-config.yaml"])
    installed = hooks.root / ".git/hooks/pre-commit"
    assert installed.exists()
    assert "sway/.pre-commit-config.yaml" in installed.read_text(encoding="utf-8")
    assert not (hooks.root / ".git/hooks/commit-msg").exists()
    config = (hooks.root / "sway/.pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "pytest" not in config
    assert "conventional" not in config.lower()
