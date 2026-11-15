"""Exercise the session CLI through external-command substitutes and real IPC."""

import socket
import subprocess
from contextlib import suppress

import pytest
from helpers import SessionSandbox, read_record, write_record


def test_start_outside_sway_refuses_before_touching_shared_services(session: SessionSandbox) -> None:
    result = session.cli("start", ok=False)
    assert "SWAYSOCK" in result.stderr
    assert session.commands() == []
    assert list(session.runtime.iterdir()) == []


def test_repeated_start_keeps_one_owner_and_explicit_helper_configuration(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    first = session.commands()
    session.cli("start")
    status = session.status()
    assert status["active"]
    assert set(status["helpers"]) == {"waybar", "swaync", "swaybg", "nm-applet", "authentication"}
    starts = [command for command in session.commands() if "start" in command]
    assert starts == [command for command in first if "start" in command]
    assert all(value == "active" for value in status["helpers"].values())
    assert not any("restart" in command for command in session.commands())


def test_stop_is_idempotent_and_leaves_unrelated_services_alone(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    session.cli("stop")
    session.cli("stop")
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}
    stopped = [command for command in session.commands() if "stop" in command]
    assert stopped
    assert not any("unrelated.service" in command or "graphical-session.target" in command for command in stopped)


@pytest.mark.parametrize("definitions", [{}, {"waybar": ["changed-nonexistent-executable"]}])
def test_changed_definitions_do_not_redefine_session_ownership(
    session: SessionSandbox, definitions: dict[str, list[str]]
) -> None:
    session.compositor()
    session.cli("start")
    write_record(session.config / "helpers.json", definitions)
    write_record(session.config / "session.json", {"helpers": [], "authentication": {"owner": "external"}})
    assert session.status()["helpers"]["waybar"] == "active"
    before = session.commands()
    session.cli("start")
    assert not any("start" in command or "stop" in command for command in session.commands()[len(before) :])
    session.cli("stop")
    assert session.status()["helpers"] == {}
    assert not session.record.exists()
    assert not (session.units / "dotfiles-sway-helper@waybar.service").exists()


def test_inconsistent_ownership_refuses_without_stopping_unverified_units(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    state = read_record(session.record)
    del state["unit_files"]["dotfiles-sway-helper@waybar.service"]
    write_record(session.record, state)
    evidence = session.record.read_bytes()
    before = session.commands()
    result = session.cli("stop", ok=False)
    assert "Traceback" not in result.stderr
    assert session.record.read_bytes() == evidence
    assert not any("stop" in command for command in session.commands()[len(before) :])
    assert (session.record.parent / "environment").exists()


def test_malformed_helper_arguments_are_a_sanitized_refusal_before_mutation(session: SessionSandbox) -> None:
    session.compositor()
    write_record(session.config / "helpers.json", {"waybar": 42})
    result = session.cli("start", ok=False)
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("Sway session refused/failed:")
    assert not any("start" in command or "stop" in command for command in session.commands())
    assert not session.record.exists()


def test_guard_acknowledges_subscription_then_exits_when_compositor_disappears(session: SessionSandbox) -> None:
    peer = session.compositor()
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notify:
        notify.bind(str(session.runtime / "notify.sock"))
        notify.settimeout(3)
        process = session.spawn("guard", NOTIFY_SOCKET=str(session.runtime / "notify.sock"))
        assert notify.recv(1024) == b"READY=1"
        assert peer.subscribed.is_set()
        peer.close()  # Abrupt loss: no shutdown event is sent.
        stdout, stderr = process.communicate(timeout=3)
        assert process.returncode == 0, stdout + stderr


@pytest.mark.parametrize(
    ("variable", "owner"),
    [
        ("FAKE_PROCESSES", "polkit-gnome-au"),
        ("FAKE_UNIT_FILES", "hyprpolkitagent.service disabled"),
        ("FAKE_BUS_NAMES", "org.kde.Polkit1 - - - (activatable)"),
    ],
)
def test_session_agent_refuses_existing_process_service_or_dbus_owner(
    session: SessionSandbox, variable: str, owner: str
) -> None:
    session.compositor()
    result = session.cli("start", ok=False, env=dict(session.env, **{variable: owner}))
    assert "authentication" in result.stderr
    assert not any("start" in command for command in session.commands())


def test_existing_dbus_authentication_is_not_activated_or_owned_by_sway(session: SessionSandbox) -> None:
    session.compositor()
    policy = session.config / "session.json"
    content = read_record(policy)
    content["authentication"] = {"owner": "external", "bus_name": "org.kde.Polkit1"}
    write_record(policy, content)
    session.env["FAKE_BUS_NAMES"] = "org.kde.Polkit1 321 agent user :1.2 - -"
    session.cli("start")
    assert "authentication" not in session.status()["helpers"]
    session.cli("stop")
    assert not any("dotfiles-sway-helper@authentication.service" in command for command in session.commands())


def test_sway_refreshes_activation_and_pins_wlr_gtk_without_global_config_edits(session: SessionSandbox) -> None:
    session.compositor()
    session.env["HYPRLAND_INSTANCE_SIGNATURE"] = "stale-hyprland"
    session.cli("start")
    environment = session.status()["environment"]
    assert environment["XDG_CURRENT_DESKTOP"] == "sway"
    assert environment["WAYLAND_DISPLAY"] == "wayland-test"
    assert environment["HYPRLAND_INSTANCE_SIGNATURE"] == ""
    updates = [command for command in session.commands() if command[0] == "dbus-update-activation-environment"]
    assert any("XDG_CURRENT_DESKTOP=sway" in command for command in updates)
    assert not any(value.startswith("XDG_CONFIG_HOME=") for command in updates for value in command)
    assert str(session.config / "portals") in session.dropin.read_text(encoding="utf-8")
    assert not (session.root / ".config/xdg-desktop-portal").exists()
    session.cli("stop")
    assert not session.dropin.exists()
    assert session.status()["environment"]["SWAYSOCK"] == ""


def test_changed_portal_override_is_preserved_without_starting_anything(session: SessionSandbox) -> None:
    session.compositor()
    session.dropin.parent.mkdir(parents=True)
    session.dropin.write_text("# other user work\n", encoding="utf-8")
    result = session.cli("start", ok=False)
    assert "Portal override changed" in result.stderr
    assert session.dropin.read_text(encoding="utf-8") == "# other user work\n"
    assert not any("start" in command for command in session.commands())


def test_return_to_hyprland_refreshes_its_environment_without_sway_helpers(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    session.cli("stop")
    session.env.update(
        HYPRLAND_INSTANCE_SIGNATURE="current-hyprland",
        WAYLAND_DISPLAY="wayland-hyprland",
        XDG_CURRENT_DESKTOP="Hyprland",
    )
    session.cli("refresh-hyprland")
    status = session.status()
    assert not status["active"]
    assert status["environment"]["SWAYSOCK"] == ""
    assert status["environment"]["XDG_CURRENT_DESKTOP"] == "Hyprland"
    assert status["environment"]["HYPRLAND_INSTANCE_SIGNATURE"] == "current-hyprland"
    assert any(
        "xdg-desktop-portal-hyprland.service" in command and "start" in command for command in session.commands()
    )
    assert status["helpers"] == {}


def test_failed_activation_retains_evidence_until_both_environments_can_be_cleared(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start", ok=False, env=dict(session.env, FAIL_DBUS="1"))
    status = session.status()
    assert not status["active"]
    assert status["helpers"]
    assert all(value == "inactive" for value in status["helpers"].values())
    assert not session.dropin.exists()
    session.cli("stop")
    assert session.status()["helpers"] == {}


def test_unowned_helper_is_not_replaced_or_duplicated(session: SessionSandbox) -> None:
    session.compositor()
    result = session.cli("start", ok=False, env=dict(session.env, FAKE_PROCESSES="swaync\nnm-applet"))
    assert "Unowned helper" in result.stderr
    assert not any("start" in command or "stop" in command for command in session.commands())


@pytest.mark.parametrize(
    ("helper", "configuration"), [("waybar", "waybar/config.jsonc"), ("swaync", "swaync/config.json")]
)
def test_helpers_receive_sway_paths_not_shared_hyprland_defaults(
    session: SessionSandbox, helper: str, configuration: str
) -> None:
    session.compositor()
    session.cli("start")
    text = (session.units / f"dotfiles-sway-helper@{helper}.service").read_text(encoding="utf-8")
    command = next(line for line in text.splitlines() if line.startswith("ExecStart="))
    assert f'ExecStart="{session.bin / helper}" "--config" "{session.config / configuration}"' in command
    assert f'"--style" "{session.config / f"styles/{helper}.css"}"' in command


def test_helper_start_failure_unwinds_ownership_and_allows_a_clean_retry(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start", ok=False, env=dict(session.env, FAIL_START="dotfiles-sway-helper@swaync.service"))
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}
    session.cli("start")
    assert session.status()["active"]


def test_compositor_loss_during_startup_does_not_leave_helpers_or_activation(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start", ok=False, env=dict(session.env, LOSE_TARGET_DURING_IMPORT="1"))
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}
    assert status["environment"]["SWAYSOCK"] == ""


def test_partial_dbus_import_is_not_a_successful_session_start(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start", ok=False, env=dict(session.env, FAIL_MANAGER_IMPORT="1"))
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}
    # The manager kept its old values, but the successful D-Bus half-import needs clearing.
    assert any(
        command[0] == "dbus-update-activation-environment" and "SWAYSOCK=" in command for command in session.commands()
    )


def test_delayed_cleanup_does_not_clear_hyprland_with_a_stale_sway_socket(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    subprocess.run(
        [
            str(session.bin / "systemctl"),
            "--user",
            "set-environment",
            "XDG_CURRENT_DESKTOP=Hyprland",
            "WAYLAND_DISPLAY=wayland-new",
        ],
        env=session.env,
        check=True,
        capture_output=True,
        timeout=15,
    )
    session.cli("stop")
    environment = session.status()["environment"]
    assert environment["XDG_CURRENT_DESKTOP"] == "Hyprland"
    assert environment["WAYLAND_DISPLAY"] == "wayland-new"


def test_portal_transition_stops_an_old_inflight_activation(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start", env=dict(session.env, OLD_PORTAL_ACTIVATING="1"))
    assert any("stop" in command and "xdg-desktop-portal.service" in command for command in session.commands())


def test_concurrent_stop_waits_for_start_before_stopping_its_helpers(session: SessionSandbox) -> None:
    session.compositor()
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as gate,
        socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notice,
    ):
        gate.bind(str(session.runtime / "start-gate"))
        gate.listen()
        gate.settimeout(5)
        notice.bind(str(session.runtime / "stop-notice"))
        notice.settimeout(0.5)
        start = session.spawn("start", START_GATE=str(session.runtime / "start-gate"))
        connection, _ = gate.accept()
        with connection:
            assert connection.recv(100) == b"startup before units"
            stop = session.spawn("stop", STOP_NOTICE=str(session.runtime / "stop-notice"))
            # Accept either schedule, then check the final public outcome, not a lock.
            with suppress(TimeoutError):
                notice.recv(100)
            connection.sendall(b"x")
        for process in (start, stop):
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stdout + stderr
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}


def test_surviving_owned_writer_keeps_recovery_evidence_and_blocks_a_new_owner(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    result = session.cli("stop", ok=False, env=dict(session.env, SURVIVING_HELPER="waybar"))
    assert "owned processes" in result.stderr
    assert session.status()["helpers"]
    session.cli("start", ok=False)
    session.cli("stop")
    assert session.status()["helpers"] == {}


def test_missing_helper_executable_fails_before_any_session_resource_starts(session: SessionSandbox) -> None:
    session.compositor()
    (session.bin / "waybar").unlink()
    result = session.cli("start", ok=False)
    assert "executable" in result.stderr
    assert not any("start" in command for command in session.commands())


def test_helper_exit_after_exec_is_reported_and_unwound(session: SessionSandbox) -> None:
    session.compositor()
    result = session.cli("start", ok=False, env=dict(session.env, EARLY_HELPER_EXIT="swaync"))
    assert "helper exited" in result.stderr
    status = session.status()
    assert not status["active"]
    assert status["helpers"] == {}


def test_status_reads_systemd_json_mapping_without_leaking_unrelated_values(session: SessionSandbox) -> None:
    subprocess.run(
        [
            str(session.bin / "systemctl"),
            "--user",
            "set-environment",
            "WAYLAND_DISPLAY=display with spaces=and-equals",
            "UNRELATED_SECRET=must-not-appear",
        ],
        env=session.env,
        check=True,
        capture_output=True,
        timeout=15,
    )
    result = session.cli("status")
    assert session.status()["environment"]["WAYLAND_DISPLAY"] == "display with spaces=and-equals"
    assert "must-not-appear" not in result.stdout
