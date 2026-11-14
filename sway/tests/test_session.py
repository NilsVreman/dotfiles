"""Exercise the public session command; never use the real user bus or desktop.

The substitutes below model external commands, not Python collaborators. IPC is
served by a private Unix socket. These checks cannot validate systemd's actual
dependency engine, portals, GDM, or polkit registration on the machine.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import unittest


CONFIGURATION = Path(__file__).resolve().parents[1] / "configuration"


class Compositor:
    """Small real IPC peer: version replies plus a shutdown subscription."""

    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(path))
        self.socket.listen()
        self.socket.settimeout(0.1)
        self.stopped = threading.Event()
        self.subscribed = threading.Event()
        self.connections = []
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        while not self.stopped.is_set():
            try:
                connection, _ = self.socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.connections.append(connection)
            header = connection.recv(14)
            if len(header) != 14:
                continue
            _, length, kind = struct.unpack("<6sII", header)
            connection.recv(length)
            payload = json.dumps({"success": True} if kind == 2 else {
                "human_readable": "sway test peer", "variant": "sway",
            }).encode()
            connection.sendall(struct.pack("<6sII", b"i3-ipc", len(payload), kind) + payload)
            if kind == 2:
                self.subscribed.set()
            else:
                connection.close()

    def close(self):
        self.stopped.set()
        self.socket.close()
        for connection in self.connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        self.thread.join(timeout=2)


class Session(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sway-session-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "configuration"
        if CONFIGURATION.exists():
            shutil.copytree(CONFIGURATION, self.config)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands.jsonl"
        # Every external command used by this entry point must be substituted.
        # Do not inherit PATH or the live bus, display, or compositor variables.
        self.env = {
            "HOME": str(self.root), "XDG_RUNTIME_DIR": str(self.runtime),
            "PATH": str(self.bin), "COMMAND_LOG": str(self.log),
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent-test-bus",
            "FAKE_MANAGER": str(self.root / "manager.json"),
        }
        substitute = self.root / "command.py"
        substitute.write_text('''#!/usr/bin/python3
import json, os, pathlib, sys
name, args = pathlib.Path(sys.argv[0]).name, sys.argv[1:]
with open(os.environ["COMMAND_LOG"], "a") as log:
    log.write(json.dumps([name, *args]) + "\\n")
path = pathlib.Path(os.environ["FAKE_MANAGER"])
state = json.loads(path.read_text()) if path.exists() else {
    "units": {"unrelated.service": "active"}, "environment": {}}
if name == "systemctl":
    args = [arg for arg in args if not arg.startswith("--")]
    verb, values = args[0], args[1:]
    if verb == "is-active":
        active = state["units"].get(values[0], "inactive")
        print(active)
        sys.exit(0 if active == "active" else 3)
    if verb == "show-environment":
        print("\\n".join(f"{key}={value}" for key, value in state["environment"].items()))
    elif verb == "show":
        print("loaded" if "--property=LoadState" in sys.argv
              else state["units"].get(values[0], "inactive"))
    elif verb == "set-environment":
        state["environment"].update(value.split("=", 1) for value in values)
    elif verb == "unset-environment":
        for value in values:
            state["environment"].pop(value, None)
    elif verb == "start":
        if os.environ.get("FAIL_START") in values:
            sys.exit(19)
        for value in values:
            state["units"][value] = "active"
    elif verb == "stop":
        for value in values:
            state["units"][value] = "inactive"
            if value == "dotfiles-sway-session.target":
                for unit in state["units"]:
                    if unit.startswith("dotfiles-sway-"):
                        state["units"][unit] = "inactive"
    elif verb in ("list-unit-files", "list-units"):
        print(os.environ.get("FAKE_UNIT_FILES", ""))
    path.write_text(json.dumps(state))
elif name == "ps":
    print(os.environ.get("FAKE_PROCESSES", ""))
elif name == "busctl":
    print(os.environ.get("FAKE_BUS_NAMES", ""))
elif name == "dbus-update-activation-environment":
    if os.environ.get("FAIL_DBUS"):
        sys.exit(23)
    state["environment"].update(value.split("=", 1) for value in args if "=" in value)
    if os.environ.get("LOSE_TARGET_DURING_IMPORT"):
        state["units"]["dotfiles-sway-session.target"] = "inactive"
    path.write_text(json.dumps(state))
''')
        substitute.chmod(0o700)
        for name in ("systemctl", "dbus-update-activation-environment", "busctl", "ps", "waybar", "swaync"):
            (self.bin / name).symlink_to(substitute)

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run(
            ["/usr/bin/python3", str(self.config / "scripts" / "session.py"), *args],
            env=env or self.env, capture_output=True, text=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def compositor(self):
        path = self.runtime / "sway.sock"
        peer = Compositor(path)
        self.addCleanup(peer.close)
        self.env.update(SWAYSOCK=str(path), WAYLAND_DISPLAY="wayland-test",
                        DISPLAY=":test", XDG_CURRENT_DESKTOP="sway",
                        XDG_SESSION_TYPE="wayland", XDG_SESSION_DESKTOP="sway")
        return peer

    def test_start_outside_sway_refuses_before_touching_shared_services(self):
        result = self.cli("start", ok=False)
        self.assertIn("SWAYSOCK", result.stderr)
        self.assertEqual(self.commands(), [])
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_repeated_start_keeps_one_owner_and_explicit_helper_configuration(self):
        self.compositor()
        self.cli("start")
        first = self.commands()
        self.cli("start")
        status = json.loads(self.cli("status").stdout)
        self.assertTrue(status["active"])
        self.assertEqual(set(status["helpers"]), {"waybar", "swaync", "swaybg", "nm-applet", "authentication"})
        starts = [command for command in self.commands() if "start" in command]
        self.assertEqual(starts, [command for command in first if "start" in command])
        self.assertTrue(all(value == "active" for value in status["helpers"].values()))
        self.assertFalse(any("restart" in command for command in self.commands()))

    def test_stop_is_idempotent_and_leaves_unrelated_services_alone(self):
        self.compositor()
        self.cli("start")
        self.cli("stop")
        self.cli("stop")
        status = json.loads(self.cli("status").stdout)
        self.assertFalse(status["active"])
        self.assertEqual(status["helpers"], {})
        stopped = [command for command in self.commands() if "stop" in command]
        self.assertTrue(stopped)
        self.assertFalse(any("unrelated.service" in command for command in stopped))
        self.assertFalse(any("graphical-session.target" in command for command in stopped))

    def test_guard_acknowledges_subscription_then_exits_when_compositor_disappears(self):
        peer = self.compositor()
        notify = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.addCleanup(notify.close)
        notify.bind(str(self.runtime / "notify.sock"))
        notify.settimeout(3)
        environment = dict(self.env, NOTIFY_SOCKET=str(self.runtime / "notify.sock"))
        process = subprocess.Popen(
            ["/usr/bin/python3", str(self.config / "scripts" / "session.py"), "guard"],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        self.assertEqual(notify.recv(1024), b"READY=1")
        self.assertTrue(peer.subscribed.is_set())
        peer.close()  # Also models abrupt loss: no shutdown event is sent.
        stdout, stderr = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0, stdout + stderr)

    def test_session_agent_refuses_existing_process_service_or_dbus_owner(self):
        self.compositor()
        for variable, owner in (
            ("FAKE_PROCESSES", "polkit-gnome-au"),
            ("FAKE_UNIT_FILES", "hyprpolkitagent.service disabled"),
            ("FAKE_BUS_NAMES", "org.kde.Polkit1 - - - (activatable)"),
        ):
            with self.subTest(owner=owner):
                result = self.cli("start", ok=False, env=dict(self.env, **{variable: owner}))
                self.assertIn("authentication", result.stderr)
                self.assertFalse(any("start" in command for command in self.commands()))

    def test_existing_dbus_authentication_is_not_activated_or_owned_by_sway(self):
        self.compositor()
        policy = self.config / "session.json"
        content = json.loads(policy.read_text())
        content["authentication"] = {"owner": "external", "bus_name": "org.kde.Polkit1"}
        policy.write_text(json.dumps(content))
        self.env["FAKE_BUS_NAMES"] = "org.kde.Polkit1 321 agent user :1.2 - -"
        self.cli("start")
        self.assertNotIn("authentication", json.loads(self.cli("status").stdout)["helpers"])
        self.cli("stop")
        self.assertFalse(any("dotfiles-sway-helper@authentication.service" in command
                             for command in self.commands()))

    def test_sway_refreshes_activation_and_pins_wlr_gtk_without_global_config_edits(self):
        self.compositor()
        self.env["HYPRLAND_INSTANCE_SIGNATURE"] = "stale-hyprland"
        self.cli("start")
        environment = json.loads(self.cli("status").stdout)["environment"]
        self.assertEqual(environment["XDG_CURRENT_DESKTOP"], "sway")
        self.assertEqual(environment["WAYLAND_DISPLAY"], "wayland-test")
        self.assertEqual(environment["HYPRLAND_INSTANCE_SIGNATURE"], "")
        updates = [command for command in self.commands()
                   if command[0] == "dbus-update-activation-environment"]
        self.assertTrue(any("XDG_CURRENT_DESKTOP=sway" in command for command in updates))
        self.assertFalse(any(value.startswith("XDG_CONFIG_HOME=")
                             for command in updates for value in command))
        dropin = (self.runtime / "systemd/user/xdg-desktop-portal.service.d"
                  / "90-dotfiles-desktop.conf")
        self.assertIn(str(self.config / "portals"), dropin.read_text())
        self.assertFalse((self.root / ".config/xdg-desktop-portal").exists())
        self.cli("stop")
        self.assertFalse(dropin.exists())
        self.assertEqual(json.loads(self.cli("status").stdout)["environment"]["SWAYSOCK"], "")

    def test_changed_portal_override_is_preserved_without_starting_anything(self):
        self.compositor()
        dropin = (self.runtime / "systemd/user/xdg-desktop-portal.service.d"
                  / "90-dotfiles-desktop.conf")
        dropin.parent.mkdir(parents=True)
        dropin.write_text("# other user work\n")
        result = self.cli("start", ok=False)
        self.assertIn("Portal override changed", result.stderr)
        self.assertEqual(dropin.read_text(), "# other user work\n")
        self.assertFalse(any("start" in command for command in self.commands()))

    def test_return_to_hyprland_refreshes_its_environment_without_sway_helpers(self):
        self.compositor()
        self.cli("start")
        self.cli("stop")
        self.env.update(HYPRLAND_INSTANCE_SIGNATURE="current-hyprland",
                        WAYLAND_DISPLAY="wayland-hyprland", XDG_CURRENT_DESKTOP="Hyprland")
        self.cli("refresh-hyprland")
        status = json.loads(self.cli("status").stdout)
        self.assertFalse(status["active"])
        self.assertEqual(status["environment"]["SWAYSOCK"], "")
        self.assertEqual(status["environment"]["XDG_CURRENT_DESKTOP"], "Hyprland")
        self.assertEqual(status["environment"]["HYPRLAND_INSTANCE_SIGNATURE"], "current-hyprland")
        self.assertTrue(any("xdg-desktop-portal-hyprland.service" in command
                            and "start" in command for command in self.commands()))
        self.assertEqual(status["helpers"], {})

    def test_failed_activation_unwinds_runtime_override_and_owned_target(self):
        self.compositor()
        self.cli("start", ok=False, env=dict(self.env, FAIL_DBUS="1"))
        status = json.loads(self.cli("status").stdout)
        self.assertFalse(status["active"])
        self.assertEqual(status["helpers"], {})
        dropin = (self.runtime / "systemd/user/xdg-desktop-portal.service.d"
                  / "90-dotfiles-desktop.conf")
        self.assertFalse(dropin.exists())

    def test_unowned_helper_is_not_replaced_or_duplicated(self):
        self.compositor()
        result = self.cli("start", ok=False, env=dict(self.env, FAKE_PROCESSES="swaync\nnm-applet"))
        self.assertIn("Unowned helper", result.stderr)
        self.assertFalse(any("start" in command or "stop" in command
                             for command in self.commands()))

    def test_helpers_receive_sway_paths_not_shared_hyprland_defaults(self):
        self.cli("run-helper", "waybar")
        self.cli("run-helper", "swaync")
        self.assertIn(["waybar", "--config", str(self.config / "waybar/config.jsonc"),
                       "--style", str(self.config / "styles/waybar.css")], self.commands())
        self.assertIn(["swaync", "--config", str(self.config / "swaync/config.json"),
                       "--style", str(self.config / "styles/swaync.css")], self.commands())

    def test_helper_start_failure_unwinds_ownership_and_allows_a_clean_retry(self):
        self.compositor()
        self.cli("start", ok=False, env=dict(self.env, FAIL_START="dotfiles-sway-helper@swaync.service"))
        status = json.loads(self.cli("status").stdout)
        self.assertFalse(status["active"])
        self.assertEqual(status["helpers"], {})
        self.cli("start")
        self.assertTrue(json.loads(self.cli("status").stdout)["active"])

    def test_compositor_loss_during_startup_does_not_leave_helpers_or_activation(self):
        self.compositor()
        self.cli("start", ok=False, env=dict(self.env, LOSE_TARGET_DURING_IMPORT="1"))
        status = json.loads(self.cli("status").stdout)
        self.assertFalse(status["active"])
        self.assertEqual(status["helpers"], {})
        self.assertEqual(status["environment"]["SWAYSOCK"], "")


if __name__ == "__main__":
    unittest.main()
