"""Model external commands only; never contact a real user manager or bus."""

import json
import os
import socket
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NotRequired, TypedDict


class _Manager(TypedDict):
    units: dict[str, str]
    environment: dict[str, str]
    bus_environment: NotRequired[dict[str, str]]


def _systemctl(state: _Manager, arguments: Sequence[str]) -> None:
    args = [arg for arg in arguments if not arg.startswith("--")]
    verb, values = args[0], args[1:]
    if verb == "link" and os.environ.get("START_GATE"):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as gate:
            gate.connect(os.environ["START_GATE"])
            gate.sendall(b"startup before units")
            gate.recv(1)
    if verb == "is-active":
        active = state["units"].get(values[0], "inactive")
        print(active)
        sys.exit(0 if active == "active" else 3)
    if verb == "show-environment":
        print(os.environ.get("MANAGER_ENVIRONMENT_JSON", json.dumps(state["environment"])))
    elif verb == "show":
        if "--property=LoadState" in arguments:
            print(os.environ.get("FAKE_LOAD_STATE", "loaded"))
        elif "--property=ActiveState,MainPID,ControlPID,ControlGroup,TasksCurrent" in arguments:
            active = state["units"].get(values[0], "inactive")
            residual = values[0] == f"dotfiles-sway-helper@{os.environ.get('SURVIVING_HELPER')}.service"
            tasks = active == "active" or residual
            print(
                f"ActiveState={active}\nMainPID=0\nControlPID=0\n"
                f"ControlGroup={'/controlled-owned-cgroup' if tasks else ''}\nTasksCurrent={1 if tasks else 0}"
            )
        else:
            print(state["units"].get(values[0], "inactive"))
    elif verb == "set-environment":
        if os.environ.get("FAIL_MANAGER_IMPORT") and "XDG_CURRENT_DESKTOP=sway" in values:
            sys.exit(24)
        for assignment in values:
            key, value = assignment.split("=", 1)
            state["environment"][key] = value
    elif verb == "unset-environment":
        for value in values:
            state["environment"].pop(value, None)
    elif verb == "start":
        if os.environ.get("FAIL_START") in values:
            print(os.environ.get("FAIL_MESSAGE", ""), file=sys.stderr)
            sys.exit(19)
        for value in values:
            state["units"][value] = "active"
        exited = f"dotfiles-sway-helper@{os.environ.get('EARLY_HELPER_EXIT')}.service"
        if exited in values:
            state["units"][exited] = "failed"
    elif verb == "stop":
        for value in values:
            state["units"][value] = "inactive"
            if value == "dotfiles-sway-session.target":
                for unit in state["units"]:
                    if unit.startswith("dotfiles-sway-"):
                        state["units"][unit] = "inactive"
    elif verb in ("list-unit-files", "list-units"):
        print(os.environ.get("FAKE_UNIT_FILES", ""))


def main() -> None:
    name, args = sys.argv[1], sys.argv[2:]
    with Path(os.environ["COMMAND_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps([name, *args]) + "\n")
    path = Path(os.environ["FAKE_MANAGER"])
    # This is controlled test data, not a runtime recovery record.
    state: _Manager = (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else {"units": {"unrelated.service": "active"}, "environment": {}}
    )
    if os.environ.get("OLD_PORTAL_ACTIVATING") and not path.exists():
        state["units"]["xdg-desktop-portal.service"] = "activating"
    if name == "systemctl":
        _systemctl(state, args)
        path.write_text(json.dumps(state), encoding="utf-8")
        if "stop" in args and os.environ.get("STOP_NOTICE"):
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notice:
                notice.sendto(b"stop reached manager", os.environ["STOP_NOTICE"])
    elif name == "ps":
        print(os.environ.get("FAKE_PROCESSES", ""))
    elif name == "busctl":
        print(os.environ.get("FAKE_BUS_NAMES", ""))
    elif name == "dbus-update-activation-environment":
        if os.environ.get("FAIL_DBUS"):
            sys.exit(23)
        updates = dict(value.split("=", 1) for value in args if "=" in value)
        state.setdefault("bus_environment", {}).update(updates)
        if os.environ.get("LOSE_TARGET_DURING_IMPORT"):
            state["units"]["dotfiles-sway-session.target"] = "inactive"
        path.write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    main()
