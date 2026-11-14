"""Sway session entry point. See sway/DEVELOPING.md for ownership and ordering.

Only invoking this command from an authorized graphical login changes the user
manager. Merely deploying the configuration does not start services.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import stat
import struct
import subprocess
import sys


CONFIG = Path(__file__).resolve().parents[1]
TARGET = "dotfiles-sway-session.target"
GUARD = "dotfiles-sway-guard.service"
FINALIZER = "dotfiles-sway-cleanup.service"
PORTAL = "xdg-desktop-portal.service"
BACKENDS = ("xdg-desktop-portal-wlr.service", "xdg-desktop-portal-gtk.service",
            "xdg-desktop-portal-hyprland.service")
ENVIRONMENT = (
    "WAYLAND_DISPLAY", "DISPLAY", "SWAYSOCK", "I3SOCK", "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE", "HYPRLAND_INSTANCE_SIGNATURE",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def command(*args, check=True, timeout=20):
    """Bound every control-plane call; never inherit its output as a shell script."""
    return subprocess.run(args, check=check, capture_output=True, text=True, timeout=timeout)


def systemctl(*args, check=True, timeout=20):
    return command("systemctl", "--user", *args, check=check, timeout=timeout)


def runtime():
    """Only our subdirectory is writable; reject a surprising/symlinked runtime."""
    path = Path(os.environ["XDG_RUNTIME_DIR"])
    require(path.is_absolute() and path.is_dir() and not path.is_symlink()
            and path.stat().st_uid == os.getuid()
            and stat.S_IMODE(path.stat().st_mode) == 0o700,
            "XDG_RUNTIME_DIR must be an owned, mode-0700 directory")
    directory = path / "dotfiles-sway-session"
    directory.mkdir(mode=0o700, exist_ok=True)
    require(not directory.is_symlink() and directory.stat().st_uid == os.getuid()
            and stat.S_IMODE(directory.stat().st_mode) == 0o700,
            "Session runtime directory must be owned and mode 0700")
    return directory


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def read_state(directory):
    path = directory / "session.json"
    return json.loads(path.read_text()) if path.exists() else None


def active(unit):
    return systemctl("is-active", "--quiet", unit, check=False).returncode == 0


def helper_unit(name):
    require(name in json.loads((CONFIG / "helpers.json").read_text()),
            f"Unknown owned helper: {name}")
    return f"dotfiles-sway-helper@{name}.service"


def receive(connection):
    """Read one framed Sway IPC message, including short stream reads."""
    def exactly(length):
        data = b""
        while len(data) < length:
            chunk = connection.recv(length - len(data))
            if not chunk:
                raise EOFError("Compositor IPC closed")
            data += chunk
        return data

    magic, length, kind = struct.unpack("<6sII", exactly(14))
    require(magic == b"i3-ipc" and length <= 1024 * 1024, "Invalid Sway IPC frame")
    return kind, json.loads(exactly(length))


def connect(kind, payload=b""):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(5)
    connection.connect(os.environ["SWAYSOCK"])
    connection.sendall(struct.pack("<6sII", b"i3-ipc", len(payload), kind) + payload)
    return connection


def validate_sway():
    require(os.environ.get("SWAYSOCK"), "SWAYSOCK is required; run start inside Sway")
    require(os.environ.get("WAYLAND_DISPLAY"), "WAYLAND_DISPLAY is required")
    with connect(7) as connection:  # GET_VERSION, not a compositor-changing command
        _, version = receive(connection)
    require(version.get("variant") == "sway", "IPC peer is not standard Sway")


def write_environment(directory):
    """Pin helper configuration/environment even if the user manager later changes."""
    values = {name: os.environ.get(name, "") for name in ENVIRONMENT}
    values.update(XDG_CURRENT_DESKTOP="sway", XDG_SESSION_DESKTOP="sway",
                  XDG_SESSION_TYPE="wayland", HYPRLAND_INSTANCE_SIGNATURE="",
                  DOTFILES_SWAY_CONFIG=str(CONFIG))
    def quote(value):
        require(not any(character in value for character in "\n\r\0"), "Invalid environment value")
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    text = "".join(f"{name}={quote(value)}\n" for name, value in values.items())
    path = directory / "environment"
    path.write_text(text)
    path.chmod(0o600)
    return values


def manager_environment():
    """Read only desktop keys; never print the manager's unrelated secrets."""
    values = dict(line.split("=", 1) for line in systemctl("show-environment").stdout.splitlines()
                  if "=" in line)
    return {name: values.get(name, "") for name in ENVIRONMENT}


def import_environment(values):
    # dbus-daemon has its own activation environment; dbus-broker uses systemd's.
    # Explicit empty values clear stale desktop identifiers in both implementations.
    command("dbus-update-activation-environment", "--systemd",
            *(f"{name}={value}" for name, value in values.items() if name in ENVIRONMENT))


def portal_override():
    """Override only the portal frontend's config home, never the user's globally."""
    path = (Path(os.environ["XDG_RUNTIME_DIR"]) / "systemd/user"
            / f"{PORTAL}.d/90-dotfiles-desktop.conf")
    value = json.dumps(f"XDG_CONFIG_HOME={CONFIG / 'portals'}", ensure_ascii=False).replace("%", "%%")
    text = "# Owned by dotfiles Sway session.py; runtime only.\n[Service]\nEnvironment=" + value + "\n"
    return path, text


def check_portals(desktop):
    path, text = portal_override()
    require(not any(parent.is_symlink() for parent in path.parents)
            and not path.is_symlink(), "Refusing a symlinked portal override path")
    require(not path.exists() or path.read_text() == text,
            "Portal override changed; refusing to overwrite user work")
    backend = "wlr" if desktop == "sway" else "hyprland"
    for unit in (PORTAL, f"xdg-desktop-portal-{backend}.service",
                 "xdg-desktop-portal-gtk.service"):
        require(systemctl("show", "--property=LoadState", "--value", unit).stdout.strip() == "loaded",
                f"Required portal unit is unavailable: {unit}")


def stop_portals(backends=BACKENDS):
    """These shared desktop brokers are the only non-owned units transitioned.

    This is supported ONLY across logout/login, not concurrent graphical sessions.
    No wildcards, PipeWire, keyrings, polkit authority, or unrelated services.
    """
    units = [unit for unit in (PORTAL, *backends) if active(unit)]
    if units:
        systemctl("stop", *units)


def activate_portals(desktop, values):
    stop_portals()
    path, text = portal_override()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(text)
    path.chmod(0o600)
    import_environment(values)
    systemctl("daemon-reload")
    backend = "wlr" if desktop == "sway" else "hyprland"
    systemctl("start", f"xdg-desktop-portal-{backend}.service",
              "xdg-desktop-portal-gtk.service")
    systemctl("start", PORTAL)


def authentication_owner(policy):
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
            acquired = command("busctl", "--user", "--acquired", "list",
                               "--no-legend", "--no-pager").stdout
            names = {line.split()[0] for line in acquired.splitlines() if line.strip()}
            require(policy["bus_name"] in names, "External authentication bus name is not owned")
            return owner
        unit = policy.get("unit", "")
        scope = policy.get("scope", "user")
        require(unit.endswith(".service") and scope in {"user", "system"},
                "External authentication needs a service unit and user/system scope")
        arguments = ["systemctl"] + (["--user"] if scope == "user" else [])
        require(command(*arguments, "is-active", "--quiet", unit, check=False).returncode == 0,
                f"External authentication owner is not active: {unit}")
        return owner

    inventory = [
        command("ps", "-u", str(os.getuid()), "-o", "comm=").stdout,
        systemctl("list-unit-files", "--no-legend", "--no-pager").stdout,
        command("systemctl", "list-units", "--all", "--no-legend", "--no-pager").stdout,
        command("busctl", "--user", "list", "--no-legend", "--no-pager").stdout,
        command("busctl", "--user", "--activatable", "list",
                "--no-legend", "--no-pager").stdout,
    ]
    for line in "\n".join(inventory).splitlines():
        name = line.split()[0].lower() if line.strip() else ""
        if name in {"polkit.service", "org.freedesktop.policykit1"}:
            continue  # The authority is not an authentication agent.
        require(not any(word in name for word in ("polkit", "policykit", "authentication-agent"))
                and name not in {"gnome-shell", "cinnamon", "org.gnome.shell"},
                f"Existing/activatable authentication owner {name}; select external ownership")
    return owner


def check_unowned_helpers(helpers):
    """Refuse leftovers instead of replacing shared D-Bus names or killing peers."""
    processes = command("ps", "-u", str(os.getuid()), "-o", "comm=").stdout.splitlines()
    names = {line.strip() for line in processes}
    collisions = names.intersection((set(helpers) | {"wl-paste"}) - {"authentication"})
    require(not collisions, f"Unowned helper still running: {', '.join(sorted(collisions))}; log out first")


def start():
    validate_sway()
    directory = runtime()
    # Serialize startup and finalization so a compositor dying mid-start cannot
    # clear state before startup has finished importing/starting resources.
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(directory)
        if active(TARGET):
            require(state and state["socket"] == os.environ["SWAYSOCK"],
                    "Another Sway session owns the target; log out first")
            print("Sway helpers already owned; no reload or restart performed.")
            return
        require(state is None, "Previous ownership record remains; run stop and investigate first")
        require(not active(GUARD) and not active(FINALIZER),
                "Previous session is still stopping; wait for its cleanup")
        policy = json.loads((CONFIG / "session.json").read_text())
        helpers = policy["helpers"].copy()
        require("authentication" not in helpers, "Authentication has its own ownership policy")
        if authentication_owner(policy["authentication"]) == "session":
            helpers.append("authentication")
        units = [helper_unit(name) for name in helpers]
        check_unowned_helpers(helpers)
        check_portals("sway")
        values = write_environment(directory)
        write_json(directory / "session.json",
                   {"socket": os.environ["SWAYSOCK"], "helpers": helpers,
                    "environment": values, "environment_before": manager_environment()})
        try:
            systemctl("link", "--runtime", *map(str, sorted((CONFIG / "systemd").iterdir())))
            systemctl("daemon-reload")
            # Start the guard/finalizer first, so any later failure has an owner.
            systemctl("start", TARGET)
            activate_portals("sway", values)
            require(active(TARGET), "Compositor ownership was lost during startup")
            if units:
                systemctl("start", *units)
        except (ValueError, OSError, subprocess.SubprocessError):
            # stop waits for the finalizer, which needs this lock. Release it
            # first, including failures before the guard has reported READY.
            fcntl.flock(lock, fcntl.LOCK_UN)
            stop()
            raise
        print("Sway helpers started under their session target.")


def status():
    directory = runtime()
    state = read_state(directory)
    print(json.dumps({
        "active": active(TARGET),
        "socket": state["socket"] if state else None,
        "helpers": {name: "active" if active(helper_unit(name)) else "inactive"
                    for name in state["helpers"]} if state else {},
        "environment": manager_environment(),
    }))


def stop():
    """Stop only recorded helpers; usable from the verified recovery console."""
    directory = runtime()
    state = read_state(directory)
    if state:
        systemctl("stop", TARGET, GUARD, FINALIZER,
                  *(helper_unit(name) for name in state["helpers"]), timeout=90)
        # Also covers a partial startup before the finalizer could be activated.
        cleanup()
    print("Owned Sway helpers stopped; compositor and unrelated services untouched.")


def cleanup():
    """Finalizer hook, ordered *after* helper cgroup cleanup, not a guard hook."""
    directory = runtime()
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(directory)
        if state is None:
            return
        current = manager_environment()
        owns_environment = current["SWAYSOCK"] == state["socket"]
        if owns_environment:
            stop_portals(BACKENDS[:2])
        # A failed import can leave the old environment untouched but our override
        # installed. Remove that artifact too. Never clear a newer desktop's values.
        if owns_environment or current == state["environment_before"]:
            path, text = portal_override()
            if path.exists():
                require(not path.is_symlink() and path.read_text() == text,
                        "Portal override changed; leaving it and recovery evidence intact")
                path.unlink()
                systemctl("daemon-reload")
        if owns_environment:
            import_environment({name: "" for name in ENVIRONMENT})
            systemctl("unset-environment", *ENVIRONMENT)
        (directory / "session.json").unlink()
        (directory / "environment").unlink(missing_ok=True)


def refresh_hyprland():
    """Optional Hyprland login hook; no compositor/helper/authentication changes.

    The existing Hyprland tree is live through symlinks, so the opt-in fragment
    is shipped here rather than editing it. This command is also the explicit
    return route run in a Hyprland terminal during the authorized private trial.
    """
    require(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
            and os.environ.get("WAYLAND_DISPLAY")
            and "Hyprland" in os.environ.get("XDG_CURRENT_DESKTOP", "").split(":"),
            "Run refresh-hyprland inside the new Hyprland login")
    directory = runtime()
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not active(TARGET) and not active(GUARD) and read_state(directory) is None,
                "Sway cleanup is incomplete; recover that session before switching")
        check_portals("hyprland")
        values = {name: os.environ.get(name, "") for name in ENVIRONMENT}
        values.update(SWAYSOCK="", I3SOCK="", XDG_CURRENT_DESKTOP="Hyprland",
                      XDG_SESSION_DESKTOP="Hyprland", XDG_SESSION_TYPE="wayland")
        activate_portals("hyprland", values)
        print("Hyprland activation environment and explicit portal providers refreshed.")


def guard():
    """Hold a shutdown subscription for the compositor's lifetime.

    systemd receives READY only after Sway has accepted the subscription. EOF
    covers crashes too; BindsTo stops the target on *any* guard exit. There is
    deliberately no shell watcher, detached child, or restart of a dead session.
    """
    with connect(2, b'["shutdown"]') as connection:
        _, reply = receive(connection)
        require(reply.get("success") is True, "Sway refused shutdown subscription")
        address = os.environ["NOTIFY_SOCKET"]
        if address.startswith("@"):
            address = "\0" + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notification:
            notification.connect(address)
            notification.sendall(b"READY=1")
        connection.settimeout(None)
        try:
            receive(connection)  # The only subscribed event is shutdown.
        except (EOFError, ConnectionResetError):
            pass


def run_helper(name):
    """Keep the helper/watcher and all its children in the template's cgroup."""
    arguments = json.loads((CONFIG / "helpers.json").read_text())[name]
    arguments = [argument.replace("@CONFIG@", str(CONFIG)) for argument in arguments]
    os.execvp(arguments[0], arguments)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(
        "start", "stop", "status", "refresh-hyprland", "guard", "cleanup", "run-helper"))
    parser.add_argument("helper", nargs="?")
    args = parser.parse_args()
    if args.command == "run-helper":
        require(args.helper is not None, "A helper name is required")
        run_helper(args.helper)
    else:
        globals()[args.command.replace("-", "_")]()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, EOFError,
            subprocess.SubprocessError) as error:
        print(f"Sway session refused/failed: {error}", file=sys.stderr)
        sys.exit(1)
