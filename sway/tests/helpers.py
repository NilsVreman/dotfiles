"""Build isolated command sandboxes and decode their JSON output."""

import hashlib
import json
import os
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from contextlib import ExitStack, suppress
from pathlib import Path
from typing import Any, Final

SWAY: Final = Path(__file__).resolve().parents[1]
FIXTURES: Final = Path(__file__).parent / "fixtures"


def read_link(path: Path) -> str:
    # Assert the exact stored link text, including redundant separators.
    return os.readlink(path)  # noqa: PTH115


def parse_record(text: str) -> dict[str, Any]:
    # Test data/output is intentionally editable; Any stays at this JSON seam.
    value: dict[str, Any] = json.loads(text)
    assert isinstance(value, dict)
    return value


def read_record(path: Path) -> dict[str, Any]:
    return parse_record(path.read_text(encoding="utf-8"))


def write_record(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_manifest(run: Path, value: object) -> None:
    data = (json.dumps(value, indent=2) + "\n").encode()
    (run / "manifest.json").write_bytes(data)
    (run / "manifest.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n", encoding="utf-8")


def load_fixture(name: str, root: Path) -> dict[str, Any]:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return parse_record(text.replace("@ROOT@", str(root)))


def script(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o700)


class Compositor:
    def __init__(self, path: Path) -> None:
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(path))
        self.socket.listen()
        self.socket.settimeout(0.1)
        self.stopped = threading.Event()
        self.subscribed = threading.Event()
        self.connections: list[socket.socket] = []
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self) -> None:
        while not self.stopped.is_set():
            try:
                connection, _ = self.socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            self.connections.append(connection)
            header = connection.recv(14)
            if len(header) != 14:
                continue
            _, length, kind = struct.unpack("<6sII", header)
            connection.recv(length)
            payload = json.dumps(
                {"success": True} if kind == 2 else {"human_readable": "sway test peer", "variant": "sway"}
            ).encode()
            connection.sendall(struct.pack("<6sII", b"i3-ipc", len(payload), kind) + payload)
            if kind == 2:
                self.subscribed.set()
            else:
                connection.close()

    def close(self) -> None:
        self.stopped.set()
        self.socket.close()
        for connection in self.connections:
            with suppress(OSError):
                connection.shutdown(socket.SHUT_RDWR)
            connection.close()
        self.thread.join(timeout=2)


class DeploymentSandbox:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "checkout"
        self.sway = self.repo / "sway"
        self.sway.mkdir(parents=True)
        for name in ("deploy.sh", "deployment.py"):
            shutil.copy2(SWAY / name, self.sway / name)
        (self.sway / "config").write_text("untracked i3 reference\n", encoding="utf-8")
        (self.sway / ".private").mkdir(mode=0o700)
        (self.sway / ".private/trial-checklist.md").write_text(
            "# Controlled checklist fixture — all cases not tested\n", encoding="utf-8"
        )
        self.home = root / "home"
        self.config = self.home / ".config"
        self.config.mkdir(parents=True)
        self.external = root / "outside"
        self.bin = root / "bin"
        self.bin.mkdir()
        # The shell entry still selects python3; this substitute selects the test
        # runner's interpreter rather than silently using the host's Python.
        script(self.bin / "python3", f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n')
        for name in ("pacman", "systemctl"):
            script(self.bin / name, "#!/bin/sh\nprintf 'controlled state\\n'\n")
        for name in ("ln", "readlink", "dirname"):
            (self.bin / name).symlink_to(f"/usr/bin/{name}")
        self.env = {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.config),
            "PATH": str(self.bin),
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent-test-bus",
        }

    def cli(self, *args: str | Path, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["/bin/bash", str(self.sway / "deploy.sh"), *map(str, args)],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=20,
        )
        assert (result.returncode == 0) == ok, result.stderr + result.stdout
        return result

    def candidate(self) -> Path:
        source = self.sway / "configuration"
        source.mkdir()
        (source / "config").write_text("# future reviewed Sway configuration\n", encoding="utf-8")
        return source

    def prepare(self) -> Path:
        return Path(self.cli("prepare", "--external", self.external).stdout.strip())


class SessionSandbox:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.resources = ExitStack()
        self.config = root / "configuration"
        shutil.copytree(SWAY / "configuration", self.config, ignore=shutil.ignore_patterns("__pycache__"))
        definitions = self.config / "helpers.json"
        helpers = read_record(definitions)
        helpers["authentication"] = ["auth-test"]
        write_record(definitions, helpers)
        self.runtime = root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "commands.jsonl"
        self.env = {
            "HOME": str(root),
            "XDG_RUNTIME_DIR": str(self.runtime),
            "PATH": str(self.bin),
            "COMMAND_LOG": str(self.log),
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent-test-bus",
            "FAKE_MANAGER": str(root / "manager.json"),
        }
        substitute = root / "command.py"
        shutil.copy2(Path(__file__).parent / "substitutes/command.py", substitute)
        for name in (
            "systemctl",
            "dbus-update-activation-environment",
            "busctl",
            "ps",
            "waybar",
            "swaync",
            "swaybg",
            "nm-applet",
            "auth-test",
        ):
            script(
                self.bin / name,
                f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(substitute))} {name} "$@"\n',
            )

    @property
    def entry(self) -> list[str]:
        return [sys.executable, str(self.config / "scripts/session.py")]

    @property
    def record(self) -> Path:
        return self.runtime / "dotfiles-sway-session/session.json"

    @property
    def units(self) -> Path:
        return self.runtime / "systemd/user"

    @property
    def dropin(self) -> Path:
        return self.units / "xdg-desktop-portal.service.d/90-dotfiles-desktop.conf"

    def cli(
        self, *args: str, ok: bool = True, env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [*self.entry, *args],
            env=env if env is not None else self.env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert (result.returncode == 0) == ok, result.stderr + result.stdout
        return result

    def status(self) -> dict[str, Any]:
        return parse_record(self.cli("status").stdout)

    def commands(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        # Only the external-command substitute writes this controlled log.
        commands: list[list[str]] = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        return commands

    def compositor(self) -> Compositor:
        path = self.runtime / "sway.sock"
        peer = Compositor(path)
        self.resources.callback(peer.close)
        self.env.update(
            SWAYSOCK=str(path),
            WAYLAND_DISPLAY="wayland-test",
            DISPLAY=":test",
            XDG_CURRENT_DESKTOP="sway",
            XDG_SESSION_TYPE="wayland",
            XDG_SESSION_DESKTOP="sway",
        )
        return peer

    def spawn(self, command: str, **environment: str) -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [*self.entry, command],
            env=dict(self.env, **environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def reap() -> None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=3)

        self.resources.callback(reap)
        return process


class HookRepository:
    def __init__(self, root: Path, uv_cache: Path) -> None:
        self.root = root
        self.env = dict(
            os.environ,
            HOME=str(root),
            PRE_COMMIT_HOME=str(root / ".pre-commit-cache"),
            UV_CACHE_DIR=str(uv_cache),
            UV_OFFLINE="1",
            UV_PYTHON_DOWNLOADS="never",
            UV_PROJECT_ENVIRONMENT=str(root / "sway/.venv"),
            UV_PYTHON=sys.executable,
            # Ignore the user's Git configuration and hooks, including global hooksPath.
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_SYSTEM="/dev/null",
            GIT_AUTHOR_NAME="Isolated tests",
            GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Isolated tests",
            GIT_COMMITTER_EMAIL="test@example.invalid",
        )
        sway = root / "sway"
        sway.mkdir()
        for name in ("pyproject.toml", "uv.lock", ".pre-commit-config.yaml", "deployment.py"):
            shutil.copy2(SWAY / name, sway / name)
        for name in ("configuration/scripts", "tests"):
            shutil.copytree(SWAY / name, sway / name, ignore=shutil.ignore_patterns("__pycache__"))
        (root / ".gitignore").write_text(
            ".pre-commit-cache/\nsway/.venv/\nsway/.ruff_cache/\nsway/.mypy_cache/\n", encoding="utf-8"
        )
        (sway / "tests/unstaged.py").write_text("VALUE = 0\n", encoding="utf-8")
        (root / "outside.py").write_text("VALUE = 0\n", encoding="utf-8")
        # An explicit nested-project selection must bypass this unusable root.
        (root / "pyproject.toml").write_text(
            '[project]\nname = "wrong-root"\nversion = "0"\nrequires-python = ">=99"\n', encoding="utf-8"
        )
        self.git("init", "--initial-branch=tests")
        self.git("add", ".")
        self.git("commit", "-m", "baseline")

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run(["git", *arguments])

    def run(self, arguments: Sequence[str], *, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(arguments, cwd=self.root, env=self.env, capture_output=True, text=True, timeout=60)
        assert (result.returncode == 0) == ok, result.stderr + result.stdout
        return result

    def hooks(self, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run([sys.executable, "-m", "pre_commit", "run", "--config", "sway/.pre-commit-config.yaml"], ok=ok)

    def contents(self) -> dict[str, bytes]:
        # Observe source files, not generated caches or Git's internal bookkeeping.
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
            and not any(part in {".git", ".venv", ".ruff_cache", ".pre-commit-cache"} for part in path.parts)
        }
