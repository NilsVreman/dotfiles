"""Control a Sway session; see sway/docs/architecture.md for ownership and ordering.

Only invoking this command from an authorized graphical login changes the user
manager. Merely deploying the configuration does not start services.
"""

import argparse
import fcntl
import json
import os
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
from collections.abc import Collection, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Final, Never, NotRequired, TypedDict, cast

CONFIG: Final = Path(__file__).resolve().parents[1]
TARGET: Final = "dotfiles-sway-session.target"
GUARD: Final = "dotfiles-sway-guard.service"
FINALIZER: Final = "dotfiles-sway-cleanup.service"
PORTAL: Final = "xdg-desktop-portal.service"
BACKENDS: Final = (
    "xdg-desktop-portal-wlr.service",
    "xdg-desktop-portal-gtk.service",
    "xdg-desktop-portal-hyprland.service",
)
DESKTOP_BACKENDS: Final = {"sway": "wlr", "hyprland": "hyprland"}
ENVIRONMENT: Final = (
    "WAYLAND_DISPLAY",
    "DISPLAY",
    "SWAYSOCK",
    "I3SOCK",
    "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP",
    "XDG_SESSION_TYPE",
    "HYPRLAND_INSTANCE_SIGNATURE",
)


class _Refusal(ValueError):
    """Report a controlled failure using only a fixed, value-free message."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        # argparse's default error includes untrusted arguments.
        super().error("Invalid command-line arguments")


class _State(TypedDict):
    socket: str
    helpers: list[str]
    environment: dict[str, str]
    environment_before: dict[str, str]
    unit_files: dict[str, str]
    stopping: NotRequired[bool]


class _Authentication(TypedDict):
    owner: str
    bus_name: NotRequired[str]
    unit: NotRequired[str]
    scope: NotRequired[str]


class _Policy(TypedDict):
    helpers: list[str]
    authentication: _Authentication


def require(condition: object, message: str) -> None:
    """Refuse an unsafe operation without including input values."""
    if not condition:
        raise _Refusal(message)


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise _Refusal("Invalid JSON object")
    # JSON schema narrowing is confined to this input seam.
    return cast(dict[str, object], value)


def _string(value: object) -> str:
    if not isinstance(value, str) or "\0" in value:
        raise _Refusal("Invalid text field")
    return value


def _strings(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and "\0" not in item for item in value):
        raise _Refusal("Invalid text array")
    return cast(list[str], value)


def _string_map(value: object) -> dict[str, str]:
    return {key: _string(item) for key, item in _mapping(value).items()}


def _environment_record(value: object) -> dict[str, str]:
    values = _string_map(value)
    require(all(name in values for name in ENVIRONMENT), "Incomplete recorded desktop environment")
    require(
        not any(character in item for item in values.values() for character in "\n\r"),
        "Invalid recorded environment value",
    )
    return values


def _read_policy() -> _Policy:
    policy = _mapping(json.loads((CONFIG / "session.json").read_text(encoding="utf-8")))
    helpers = _strings(policy.get("helpers"))
    require(len(set(helpers)) == len(helpers), "Duplicate configured helper")
    for name in helpers:
        helper_unit(name)
    authentication = _mapping(policy.get("authentication"))
    require(authentication.get("owner") in ("session", "external"), "Unknown authentication owner")
    for name in ("bus_name", "unit", "scope"):
        if name in authentication:
            _string(authentication[name])
    # Required fields and all used optional fields have been validated.
    return cast(_Policy, policy)


def command(*args: str, check: bool = True, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    """Bound every control-plane call; never inherit its output as a shell script."""
    return subprocess.run(args, check=check, capture_output=True, text=True, timeout=timeout)


def systemctl(*args: str, check: bool = True, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    """Invoke only the user manager with bounded, captured output."""
    return command("systemctl", "--user", *args, check=check, timeout=timeout)


def runtime() -> Path:
    """Validate private login state; named systemd artifacts live beside it."""
    path = Path(os.environ["XDG_RUNTIME_DIR"])
    require(
        path.is_absolute()
        and path.is_dir()
        and not path.is_symlink()
        and path.stat().st_uid == os.getuid()
        and stat.S_IMODE(path.stat().st_mode) == 0o700,
        "XDG_RUNTIME_DIR must be an owned, mode-0700 directory",
    )
    directory = path / "dotfiles-sway-session"
    directory.mkdir(mode=0o700, exist_ok=True)
    require(
        not directory.is_symlink()
        and directory.stat().st_uid == os.getuid()
        and stat.S_IMODE(directory.stat().st_mode) == 0o700,
        "Session runtime directory must be owned and mode 0700",
    )
    return directory


def write_json(path: Path, value: Mapping[str, object]) -> None:
    """Replace private ownership evidence atomically."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def read_state(directory: Path) -> _State | None:
    """Validate all ownership evidence before any query or cleanup uses it."""
    path = directory / "session.json"
    try:
        state = _mapping(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        return None
    require(bool(_string(state.get("socket"))), "Missing owning compositor socket")
    helpers = _strings(state.get("helpers"))
    require(len(set(helpers)) == len(helpers), "Duplicate recorded helper")
    expected = {helper_unit(name) for name in helpers}
    units = _string_map(state.get("unit_files"))
    require(
        set(units) == expected and all(units.values()),
        "Inconsistent helper ownership evidence; recovery evidence retained",
    )
    _environment_record(state.get("environment"))
    _environment_record(state.get("environment_before"))
    require("stopping" not in state or isinstance(state["stopping"], bool), "Invalid ownership stopping flag")
    # Keep unknown fields intact when stop writes a legacy ownership record.
    return cast(_State, state)


def active(unit: str) -> bool:
    """Report manager activity without interpreting it as readiness."""
    return systemctl("is-active", "--quiet", unit, check=False).returncode == 0


def helper_unit(name: str) -> str:
    """Derive an instance name independently of mutable helper definitions."""
    # systemd instances also permit colons, literal escape text, and additional @.
    unit = f"dotfiles-sway-helper@{name}.service"
    require(re.fullmatch(r"[A-Za-z0-9:_.@\\-]+", name) and len(unit) <= 255, "Invalid owned helper name")
    return unit


def helper_commands(helpers: Sequence[str]) -> dict[str, str]:
    """Render direct ExecStart commands so Type=exec observes the TOOL's exec.

    A Python/env/shell launcher would acknowledge its own exec before discovering
    a missing helper. Runtime instance files use the shared lifecycle template,
    but systemd itself executes each resolved tool. No command is shell-evaluated.
    """
    definitions = _mapping(json.loads((CONFIG / "helpers.json").read_text(encoding="utf-8")))
    for name, value in definitions.items():
        helper_unit(name)
        arguments = _strings(value)
        require(arguments and arguments[0], "Helper command must have an executable")
    require(all(name in definitions for name in helpers), "Missing selected helper definition")
    template = (CONFIG / "systemd/dotfiles-sway-helper@.service").read_text(encoding="utf-8")
    units = {}
    for name in helpers:
        arguments = [value.replace("@CONFIG@", str(CONFIG)) for value in _strings(definitions[name])]
        executable = shutil.which(arguments[0])
        if executable is None:
            raise _Refusal("Missing helper executable")
        arguments[0] = executable
        # systemd unit syntax uses C-style quoting, % specifiers and $ expansion.
        quoted = [json.dumps(value, ensure_ascii=False).replace("%", "%%").replace("$", "$$") for value in arguments]
        text = template.replace("ExecStart=/usr/bin/false", "ExecStart=" + " ".join(quoted))
        path = Path(os.environ["XDG_RUNTIME_DIR"]) / "systemd/user" / helper_unit(name)
        require(
            not path.is_symlink() and (not path.exists() or path.read_text(encoding="utf-8") == text),
            "Owned helper unit changed; refusing to overwrite",
        )
        units[helper_unit(name)] = text
    return units


def receive(connection: socket.socket) -> tuple[int, object]:
    """Read one framed Sway IPC message, including short stream reads."""

    def exactly(length: int) -> bytes:
        data = b""
        while len(data) < length:
            chunk = connection.recv(length - len(data))
            if not chunk:
                raise EOFError("Compositor IPC closed")
            data += chunk
        return data

    magic, length, kind = struct.unpack("<6sII", exactly(14))
    require(magic == b"i3-ipc" and length <= 1024 * 1024, "Invalid Sway IPC frame")
    return int(kind), json.loads(exactly(length))


def connect(kind: int, payload: bytes = b"") -> socket.socket:
    """Connect to the selected compositor and send one framed request."""
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(5)
    connection.connect(os.environ["SWAYSOCK"])
    connection.sendall(struct.pack("<6sII", b"i3-ipc", len(payload), kind) + payload)
    return connection


def validate_sway() -> None:
    """Require a standard-Sway IPC peer without changing compositor state."""
    require(os.environ.get("SWAYSOCK"), "SWAYSOCK is required; run start inside Sway")
    require(os.environ.get("WAYLAND_DISPLAY"), "WAYLAND_DISPLAY is required")
    with connect(7) as connection:  # GET_VERSION, not a compositor-changing command
        _, version = receive(connection)
    require(_mapping(version).get("variant") == "sway", "IPC peer is not standard Sway")


def write_environment(directory: Path) -> dict[str, str]:
    """Pin helper configuration/environment even if the user manager later changes."""
    values = {name: os.environ.get(name, "") for name in ENVIRONMENT}
    values.update(
        XDG_CURRENT_DESKTOP="sway",
        XDG_SESSION_DESKTOP="sway",
        XDG_SESSION_TYPE="wayland",
        HYPRLAND_INSTANCE_SIGNATURE="",
        DOTFILES_SWAY_CONFIG=str(CONFIG),
    )

    def quote(value: str) -> str:
        require(not any(character in value for character in "\n\r\0"), "Invalid environment value")
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    text = "".join(f"{name}={quote(value)}\n" for name, value in values.items())
    path = directory / "environment"
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)
    return values


def manager_environment() -> dict[str, str]:
    """Read only desktop keys; never print the manager's unrelated secrets."""
    # Text output is shell-escaped; JSON preserves spaces/quotes in socket paths.
    raw: object = json.loads(systemctl("show-environment", "--output=json").stdout)
    values = _string_map({} if raw is None else raw)
    return {name: values.get(name, "") for name in ENVIRONMENT}


def import_environment(values: Mapping[str, str]) -> None:
    """Import and verify only desktop identity keys in both activation managers."""
    # dbus-daemon has its own activation environment; dbus-broker uses systemd's.
    # Explicit empty values clear stale desktop identifiers in both implementations.
    selected = {name: value for name, value in values.items() if name in ENVIRONMENT}
    assignments = [f"{name}={value}" for name, value in selected.items()]
    # --systemd only warns if updating the manager fails, and may still exit 0.
    # Separate checked calls make a half-import a failure, not a healthy login.
    command("dbus-update-activation-environment", *assignments)
    systemctl("set-environment", *assignments)
    current = manager_environment()
    require(
        all(current[name] == value for name, value in selected.items()),
        "systemd activation environment did not accept the desktop values",
    )


def portal_override() -> tuple[Path, str]:
    """Override only the portal frontend's config home, never the user's globally."""
    path = Path(os.environ["XDG_RUNTIME_DIR"]) / "systemd/user" / f"{PORTAL}.d/90-dotfiles-desktop.conf"
    value = json.dumps(f"XDG_CONFIG_HOME={CONFIG / 'portals'}", ensure_ascii=False).replace("%", "%%")
    text = "# Owned by dotfiles Sway session.py; runtime only.\n[Service]\nEnvironment=" + value + "\n"
    return path, text


def check_portals(desktop: str) -> None:
    """Check required providers and preserve any unowned runtime override."""
    path, text = portal_override()
    require(
        not any(parent.is_symlink() for parent in path.parents) and not path.is_symlink(),
        "Refusing a symlinked portal override path",
    )
    require(
        not path.exists() or path.read_text(encoding="utf-8") == text,
        "Portal override changed; refusing to overwrite user work",
    )
    backend = DESKTOP_BACKENDS[desktop]
    for unit in (PORTAL, f"xdg-desktop-portal-{backend}.service", "xdg-desktop-portal-gtk.service"):
        require(
            systemctl("show", "--property=LoadState", "--value", unit).stdout.strip() == "loaded",
            "Required portal unit is unavailable",
        )


def stop_portals(backends: Sequence[str] = BACKENDS) -> None:
    """These shared desktop brokers are the only non-owned units transitioned.

    This is supported ONLY across logout/login, not concurrent graphical sessions.
    No wildcards, PipeWire, keyrings, polkit authority, or unrelated services.
    """
    units = []
    for unit in (PORTAL, *backends):
        result = systemctl("show", "--property=LoadState", "--value", unit, check=False)
        if result.stdout.strip() == "not-found":
            continue
        result.check_returncode()
        require(result.stdout.strip() in {"loaded", "masked"}, "Cannot determine portal ownership/availability")
        units.append(unit)
    if units:
        # is-active omits activating/deactivating units. A synchronous stop of
        # every available named broker also cancels/joins those old jobs.
        systemctl("stop", *units)


def activate_portals(desktop: str, values: Mapping[str, str]) -> None:
    """Transition only named brokers after selecting an explicit desktop."""
    stop_portals()
    path, text = portal_override()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)
    import_environment(values)
    systemctl("daemon-reload")
    backend = DESKTOP_BACKENDS[desktop]
    systemctl("start", f"xdg-desktop-portal-{backend}.service", "xdg-desktop-portal-gtk.service")
    systemctl("start", PORTAL)


def authentication_owner(policy: _Authentication) -> str:
    """Choose one owner without activating, masking, or stopping another agent.

    Polkit has no portable enumeration of registered authentication agents. The
    inventory is intentionally conservative, including installed/activatable
    peers, but is not proof of registration. The private interactive check is
    mandatory. An unfamiliar integrated agent needs an explicit external owner.
    """
    owner = policy["owner"]
    require(owner in {"session", "external"}, "Unknown authentication owner")
    if owner == "external":
        if policy.get("bus_name"):
            require(not policy.get("unit"), "Select one external authentication owner")
            acquired = command("busctl", "--user", "--acquired", "list", "--no-legend", "--no-pager").stdout
            names = {line.split()[0] for line in acquired.splitlines() if line.strip()}
            require(policy["bus_name"] in names, "External authentication bus name is not owned")
            return owner
        unit = policy.get("unit", "")
        scope = policy.get("scope", "user")
        require(
            unit.endswith(".service") and scope in {"user", "system"},
            "External authentication needs a service unit and user/system scope",
        )
        arguments = ["systemctl"] + (["--user"] if scope == "user" else [])
        require(
            command(*arguments, "is-active", "--quiet", unit, check=False).returncode == 0,
            "External authentication owner is not active",
        )
        return owner

    inventory = [
        command("ps", "-u", str(os.getuid()), "-o", "comm=").stdout,
        systemctl("list-unit-files", "--no-legend", "--no-pager").stdout,
        command("systemctl", "list-units", "--all", "--no-legend", "--no-pager").stdout,
        command("busctl", "--user", "list", "--no-legend", "--no-pager").stdout,
        command("busctl", "--user", "--activatable", "list", "--no-legend", "--no-pager").stdout,
    ]
    for line in "\n".join(inventory).splitlines():
        name = line.split()[0].lower() if line.strip() else ""
        if name in {"polkit.service", "org.freedesktop.policykit1"}:
            continue  # The authority is not an authentication agent.
        require(
            not any(word in name for word in ("polkit", "policykit", "authentication-agent"))
            and name not in {"gnome-shell", "cinnamon", "org.gnome.shell"},
            "Existing/activatable authentication owner; select external ownership",
        )
    return owner


def check_unowned_helpers(helpers: Collection[str]) -> None:
    """Refuse leftovers instead of replacing shared D-Bus names or killing peers."""
    processes = command("ps", "-u", str(os.getuid()), "-o", "comm=").stdout.splitlines()
    names = {line.strip() for line in processes}
    collisions = names.intersection((set(helpers) | {"wl-paste"}) - {"authentication"})
    require(not collisions, "Unowned helper still running; log out first")


def start() -> None:
    """Start one session owner, or retain an existing healthy owner unchanged."""
    validate_sway()
    directory = runtime()
    # Serialize startup and finalization so a compositor dying mid-start cannot
    # clear state before startup has finished importing/starting resources.
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(directory)
        if active(TARGET):
            if state is None or state["socket"] != os.environ["SWAYSOCK"]:
                raise _Refusal("Another Sway session owns the target; log out first")
            require(not state.get("stopping"), "Sway ownership is stopping; wait for cleanup")
            require(
                all(active(helper_unit(name)) for name in state["helpers"]),
                "An owned helper failed; inspect its journal and recover before retrying",
            )
            print("Sway helpers already owned; no reload or restart performed.")
            return
        require(state is None, "Previous ownership record remains; run stop and investigate first")
        require(not active(GUARD) and not active(FINALIZER), "Previous session is still stopping; wait for its cleanup")
        policy = _read_policy()
        helpers = policy["helpers"].copy()
        require("authentication" not in helpers, "Authentication has its own ownership policy")
        if authentication_owner(policy["authentication"]) == "session":
            helpers.append("authentication")
        units = [helper_unit(name) for name in helpers]
        check_unowned_helpers(helpers)
        check_portals("sway")
        unit_files = helper_commands(helpers)
        values = write_environment(directory)
        ownership: _State = {
            "socket": os.environ["SWAYSOCK"],
            "helpers": helpers,
            "environment": values,
            "environment_before": manager_environment(),
            "unit_files": unit_files,
        }
        write_json(directory / "session.json", ownership)
        try:
            unit_directory = Path(os.environ["XDG_RUNTIME_DIR"]) / "systemd/user"
            unit_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            for unit, text in unit_files.items():
                path = unit_directory / unit
                path.write_text(text, encoding="utf-8")
                path.chmod(0o600)
            systemctl("link", "--runtime", *map(str, sorted((CONFIG / "systemd").iterdir())))
            systemctl("daemon-reload")
            # Start the guard/finalizer first, so any later failure has an owner.
            systemctl("start", TARGET)
            activate_portals("sway", values)
            require(active(TARGET), "Compositor ownership was lost during startup")
            if units:
                systemctl("start", *units)
                require(all(active(unit) for unit in units), "An owned helper exited during startup")
        except (ValueError, OSError, subprocess.SubprocessError):
            # stop waits for the finalizer, which needs this lock. Release it
            # first, including failures before the guard has reported READY.
            fcntl.flock(lock, fcntl.LOCK_UN)
            stop()
            raise
        print("Sway helpers started under their session target.")


def status() -> None:
    """Print ownership and manager activity without claiming desktop readiness."""
    directory = runtime()
    state = read_state(directory)
    print(
        json.dumps(
            {
                "active": active(TARGET),
                "socket": state["socket"] if state else None,
                "helpers": {name: "active" if active(helper_unit(name)) else "inactive" for name in state["helpers"]}
                if state
                else {},
                "environment": manager_environment(),
            }
        )
    )


def stop() -> None:
    """Stop only recorded helpers; usable from the verified recovery console."""
    directory = runtime()
    # Wait for an in-flight startup BEFORE taking the stop snapshot. Otherwise
    # we could stop inactive units, then finalize helpers started afterwards.
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(directory)
        if state:
            state["stopping"] = True
            write_json(directory / "session.json", state)
    # Do not hold the lock across this wait: the finalizer needs it too.
    if state:
        systemctl("stop", TARGET, GUARD, FINALIZER, *(helper_unit(name) for name in state["helpers"]), timeout=90)
        # Also covers a partial startup before the finalizer could be activated.
        cleanup()
    print("Owned Sway helpers stopped; compositor and unrelated services untouched.")


def verify_owned_stopped(state: _State) -> None:
    """A completed stop job is not proof that SIGKILL reaped every child.

    Task accounting includes descendants; a missing/unknown count in a remaining
    cgroup fails closed. The finalizer itself is excluded because it is running
    this check. Never discard evidence of surviving guards, watchers or writers.
    """
    properties = "ActiveState,MainPID,ControlPID,ControlGroup,TasksCurrent"
    for unit in [GUARD, *(helper_unit(name) for name in state["helpers"])]:
        output = systemctl("show", f"--property={properties}", unit).stdout
        values = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
        require(
            values.get("ActiveState") in {"inactive", "failed"}
            and values.get("MainPID") == "0"
            and values.get("ControlPID") == "0"
            and (values.get("ControlGroup") == "" or values.get("TasksCurrent") == "0"),
            "Surviving or unverifiable owned processes; recovery evidence retained",
        )


def _artifact_present(path: Path) -> bool:
    # A dangling symlink is edited evidence, not an absent artifact.
    # Other stat failures must propagate rather than being mistaken for absence.
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def cleanup() -> None:
    """Finalizer hook, ordered *after* helper cgroup cleanup, not a guard hook."""
    directory = runtime()
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(directory)
        if state is None:
            return
        verify_owned_stopped(state)
        current = manager_environment()
        # A new desktop may import its identity/display before replacing an
        # inherited SWAYSOCK. That stale single variable is not ownership.
        owns_environment = all(current[name] == state["environment"][name] for name in ENVIRONMENT)
        if owns_environment:
            stop_portals(BACKENDS[:2])
        # A failed import can leave the old environment untouched but our override
        # installed. Remove that artifact too. Never clear a newer desktop's values.
        if owns_environment or current == state["environment_before"]:
            path, text = portal_override()
            if _artifact_present(path):
                require(
                    not path.is_symlink() and path.read_text(encoding="utf-8") == text,
                    "Portal override changed; leaving it and recovery evidence intact",
                )
                path.unlink()
                systemctl("daemon-reload")
        if owns_environment or current == state["environment_before"]:
            import_environment(dict.fromkeys(ENVIRONMENT, ""))
            systemctl("unset-environment", *ENVIRONMENT)
        for unit, text in state["unit_files"].items():
            path = Path(os.environ["XDG_RUNTIME_DIR"]) / "systemd/user" / unit
            if _artifact_present(path):
                require(
                    not path.is_symlink() and path.read_text(encoding="utf-8") == text,
                    "Owned helper unit changed; preserving recovery evidence",
                )
                path.unlink()
        systemctl("daemon-reload")
        (directory / "session.json").unlink()
        (directory / "environment").unlink(missing_ok=True)


def refresh_hyprland() -> None:
    """Optional Hyprland login hook; no compositor/helper/authentication changes.

    The existing Hyprland tree is live through symlinks, so the opt-in fragment
    is shipped here rather than editing it. This command is also the explicit
    return route run in a Hyprland terminal during the authorized private trial.
    """
    require(
        os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        and os.environ.get("WAYLAND_DISPLAY")
        and "Hyprland" in os.environ.get("XDG_CURRENT_DESKTOP", "").split(":"),
        "Run refresh-hyprland inside the new Hyprland login",
    )
    directory = runtime()
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(
            not active(TARGET) and not active(GUARD) and read_state(directory) is None,
            "Sway cleanup is incomplete; recover that session before switching",
        )
        check_portals("hyprland")
        values = {name: os.environ.get(name, "") for name in ENVIRONMENT}
        values.update(
            SWAYSOCK="",
            I3SOCK="",
            XDG_CURRENT_DESKTOP="Hyprland",
            XDG_SESSION_DESKTOP="Hyprland",
            XDG_SESSION_TYPE="wayland",
        )
        activate_portals("hyprland", values)
        print("Hyprland activation environment and explicit portal providers refreshed.")


def guard() -> None:
    """Hold a shutdown subscription for the compositor's lifetime.

    systemd receives READY only after Sway has accepted the subscription. EOF
    covers crashes too; BindsTo stops the target on *any* guard exit. There is
    deliberately no shell watcher, detached child, or restart of a dead session.
    """
    with connect(2, b'["shutdown"]') as connection:
        _, reply = receive(connection)
        require(_mapping(reply).get("success") is True, "Sway refused shutdown subscription")
        address = os.environ["NOTIFY_SOCKET"]
        if address.startswith("@"):
            address = "\0" + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notification:
            notification.connect(address)
            notification.sendall(b"READY=1")
        connection.settimeout(None)
        with suppress(EOFError, ConnectionResetError):
            receive(connection)  # The only subscribed event is shutdown.


def main() -> None:
    """Dispatch the standalone command without importing installed project code."""
    os.umask(0o077)
    commands = {
        "start": start,
        "stop": stop,
        "status": status,
        "refresh-hyprland": refresh_hyprland,
        "guard": guard,
        "cleanup": cleanup,
    }
    parser = _Parser(prog="session.py", description=__doc__)
    parser.add_argument("command", choices=commands)
    args = parser.parse_args()
    commands[args.command]()


if __name__ == "__main__":
    try:
        main()
    except _Refusal as error:
        print(f"Sway session refused/failed: {error}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError, KeyError, EOFError, RecursionError, subprocess.SubprocessError):
        # Raw OS/subprocess/decoder exceptions can reproduce private input values.
        print("Sway session refused/failed: Invalid input or failed system operation", file=sys.stderr)
        sys.exit(1)
