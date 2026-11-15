"""Provide isolated homes, command substitutes, and private compositor peers."""

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from helpers import DeploymentSandbox, HookRepository, SessionSandbox


@pytest.fixture
def deployment(tmp_path: Path) -> DeploymentSandbox:
    return DeploymentSandbox(tmp_path)


@pytest.fixture
def session(tmp_path_factory: pytest.TempPathFactory) -> Iterator[SessionSandbox]:
    # A short directory keeps Unix socket names below the platform's byte limit.
    sandbox = SessionSandbox(tmp_path_factory.mktemp("session"))
    with sandbox.resources:
        yield sandbox


@pytest.fixture(scope="session")
def uv_cache() -> Path:
    # Reuse the outer locked run's cached tools rather than downloading in tests.
    result = subprocess.run(["uv", "cache", "dir"], capture_output=True, text=True, check=True, timeout=20)
    return Path(result.stdout.strip())


@pytest.fixture
def hooks(tmp_path: Path, uv_cache: Path) -> HookRepository:
    return HookRepository(tmp_path, uv_cache)
