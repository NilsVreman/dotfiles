"""Refuse malformed inputs and keep values out of command error output."""

import json

import pytest
from helpers import (
    DeploymentSandbox,
    SessionSandbox,
    load_fixture,
    read_record,
    script,
    write_manifest,
    write_record,
)


@pytest.mark.parametrize(
    ("filename", "value"),
    [
        ("session.json", []),
        ("session.json", {}),
        ("session.json", {"helpers": "private-helper", "authentication": {"owner": "session"}}),
        ("session.json", {"helpers": [42], "authentication": {"owner": "session"}}),
        ("session.json", {"helpers": [], "authentication": None}),
        ("session.json", {"helpers": [], "authentication": {"owner": ["private-owner"]}}),
        ("session.json", {"helpers": [], "authentication": {"owner": "external", "unit": []}}),
        ("helpers.json", []),
        ("helpers.json", {"waybar": []}),
        ("helpers.json", {"waybar": [""]}),
        ("helpers.json", {"waybar": [42]}),
        ("helpers.json", {"../../private-helper": ["private-command"]}),
    ],
)
def test_malformed_configuration_refuses_before_live_changes(
    session: SessionSandbox, filename: str, value: object
) -> None:
    session.compositor()
    (session.config / filename).write_text(json.dumps(value), encoding="utf-8")
    result = session.cli("start", ok=False)
    assert result.returncode == 1
    assert result.stderr.startswith("Sway session refused/failed:")
    assert "Traceback" not in result.stderr
    assert "private-" not in result.stderr
    assert not any("start" in command or "stop" in command for command in session.commands())
    assert not session.record.exists()


@pytest.mark.parametrize("command", ["status", "start", "stop", "cleanup"])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("socket", []),
        ("helpers", "private-helper"),
        ("helpers", [42]),
        ("helpers", ["../../private-helper"]),
        ("unit_files", []),
        ("unit_files", {}),
        ("environment", {}),
        ("environment_before", None),
        ("stopping", "private-flag"),
    ],
)
def test_malformed_ownership_retains_evidence_without_live_changes(
    session: SessionSandbox, command: str, field: str, value: object
) -> None:
    session.compositor()
    state = load_fixture("session-v1.json", session.root)
    state[field] = value
    session.record.parent.mkdir(mode=0o700)
    write_record(session.record, state)
    evidence = session.record.read_bytes()
    (session.record.parent / "environment").write_text("# recovery evidence\n", encoding="utf-8")
    result = session.cli(command, ok=False)
    assert result.returncode == 1
    assert result.stderr.startswith("Sway session refused/failed:")
    assert "Traceback" not in result.stderr
    assert "private-" not in result.stderr
    assert session.record.read_bytes() == evidence
    assert (session.record.parent / "environment").exists()
    assert not any("start" in entry or "stop" in entry for entry in session.commands())


@pytest.mark.parametrize("value", ["{", '["private-environment"]', '{"private-key": 42}'])
def test_malformed_manager_output_is_a_sanitized_failure(session: SessionSandbox, value: str) -> None:
    result = session.cli("status", ok=False, env=dict(session.env, MANAGER_ENVIRONMENT_JSON=value))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "private-" not in result.stderr


def test_null_manager_environment_still_means_no_values(session: SessionSandbox) -> None:
    result = session.cli("status", env=dict(session.env, MANAGER_ENVIRONMENT_JSON="null"))
    assert all(value == "" for value in json.loads(result.stdout)["environment"].values())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("nodes", []),
        ("nodes", {"../private-object": {}}),
        ("nodes", {"0": {"path": "/", "mode": 420, "kind": "private-kind"}}),
        ("nodes", {"0": {"path": "/", "mode": [], "kind": "directory", "children": {}}}),
        ("nodes", {"0": {"path": "/", "mode": 493, "kind": "directory", "children": {"../private-child": "0"}}}),
        ("nodes", {"0": {"path": "/", "mode": 493, "kind": "directory", "children": {"cycle": "0"}}}),
        ("nodes", {"0": {"path": "/", "mode": 511, "kind": "link", "link": "/", "target": "0"}}),
        ("roots", {"source": "missing-private-object", "target": None}),
    ],
)
def test_malformed_snapshot_graph_refuses_without_export_or_live_changes(
    deployment: DeploymentSandbox, field: str, value: object
) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.write_text("preserve original\n", encoding="utf-8")
    run = deployment.prepare()
    manifest = read_record(run / "manifest.json")
    manifest[field] = value
    write_manifest(run, manifest)
    export = deployment.root / "export"
    evidence = (run / "manifest.json").read_bytes()
    result = deployment.cli("verify", run, "--restore-to", export, ok=False)
    assert "Traceback" not in result.stderr
    assert "private-" not in result.stderr
    assert not export.exists()
    assert target.read_text(encoding="utf-8") == "preserve original\n"
    assert (run / "manifest.json").read_bytes() == evidence


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("phase", []),
        ("target", ["private-path"]),
        ("source", "relative-private-path"),
        ("displaced", "/private-unrelated-object"),
        ("external", None),
        ("config_identity", [1]),
        ("config_identity", [True, False]),
        ("package_changes", {}),
        ("service_changes", None),
        ("prior_state", []),
    ],
)
def test_malformed_journal_refuses_before_mutation(deployment: DeploymentSandbox, field: str, value: object) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.write_text("preserve original\n", encoding="utf-8")
    run = deployment.prepare()
    journal = read_record(run / "deployment.json")
    journal[field] = value
    write_record(run / "deployment.json", journal)
    evidence = (run / "deployment.json").read_bytes()
    result = deployment.cli("deploy", run, "--apply", ok=False)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "private-" not in result.stderr
    assert target.read_text(encoding="utf-8") == "preserve original\n"
    assert (run / "deployment.json").read_bytes() == evidence


def test_session_subprocess_errors_do_not_quote_arguments_or_stderr(session: SessionSandbox) -> None:
    session.compositor()
    session.env["WAYLAND_DISPLAY"] = "private-display-argument"
    result = session.cli(
        "start",
        ok=False,
        env=dict(
            session.env, FAIL_START="dotfiles-sway-helper@swaync.service", FAIL_MESSAGE="private-subprocess-error"
        ),
    )
    assert result.returncode == 1
    assert "private-" not in result.stderr
    assert "dotfiles-sway-helper@swaync.service" not in result.stderr
    assert "Traceback" not in result.stderr


def test_deployment_subprocess_errors_do_not_quote_paths_or_stderr(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    run = deployment.prepare()
    (deployment.bin / "ln").unlink()
    script(deployment.bin / "ln", '#!/bin/sh\nprintf "private-error %s\\n" "$@" >&2\nexit 19\n')
    result = deployment.cli("deploy", run, "--apply", ok=False)
    assert result.returncode == 1
    assert str(deployment.root) not in result.stderr
    assert "private-error" not in result.stderr
    assert "Traceback" not in result.stderr
    deployment.cli("reverse", run, "--apply")


def test_os_errors_do_not_quote_offending_paths(deployment: DeploymentSandbox, session: SessionSandbox) -> None:
    result = deployment.cli("verify", deployment.root / "private-nonexistent", ok=False)
    assert "private-nonexistent" not in result.stderr
    assert str(deployment.root) not in result.stderr
    session.env["XDG_RUNTIME_DIR"] = str(session.root / "private-nonexistent")
    result = session.cli("status", ok=False)
    assert "private-nonexistent" not in result.stderr
    assert str(session.root) not in result.stderr


def test_raw_filesystem_and_socket_errors_are_sanitized(deployment: DeploymentSandbox, session: SessionSandbox) -> None:
    deployment.candidate()
    run = deployment.prepare()
    (run / "manifest.json").unlink()
    result = deployment.cli("verify", run, ok=False)
    assert result.returncode == 1
    assert str(run) not in result.stderr
    assert "Traceback" not in result.stderr
    session.env.update(SWAYSOCK=str(session.root / "private-missing.sock"), WAYLAND_DISPLAY="private-display")
    result = session.cli("start", ok=False)
    assert result.returncode == 1
    assert "private-" not in result.stderr
    assert str(session.root) not in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("FAKE_PROCESSES", "swaync"),
        ("FAKE_UNIT_FILES", "private-authentication-agent.service disabled"),
        ("FAKE_BUS_NAMES", "private.authentication-agent - - - (activatable)"),
    ],
)
def test_inventory_refusals_do_not_repeat_offending_names(session: SessionSandbox, variable: str, value: str) -> None:
    session.compositor()
    result = session.cli("start", ok=False, env=dict(session.env, **{variable: value}))
    assert "private-" not in result.stderr
    assert "private." not in result.stderr
    assert "swaync" not in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_executable_error_does_not_quote_the_command_path(session: SessionSandbox) -> None:
    session.compositor()
    definitions = read_record(session.config / "helpers.json")
    definitions["waybar"] = ["/nonexistent/private-helper-command", "--private-argument"]
    write_record(session.config / "helpers.json", definitions)
    result = session.cli("start", ok=False)
    assert "private-" not in result.stderr
    assert "Traceback" not in result.stderr
    assert not session.record.exists()


def test_usage_errors_keep_exit_two_without_repeating_arguments(
    deployment: DeploymentSandbox, session: SessionSandbox
) -> None:
    for result in (
        deployment.cli("private-command", ok=False),
        session.cli("private-command", ok=False),
    ):
        assert result.returncode == 2
        assert "private-command" not in result.stderr
        assert "usage:" in result.stderr
        assert "Traceback" not in result.stderr


def test_edited_runtime_unit_is_preserved_with_recovery_evidence(session: SessionSandbox) -> None:
    session.compositor()
    session.cli("start")
    path = session.units / "dotfiles-sway-helper@waybar.service"
    path.write_text("# private edited unit\n", encoding="utf-8")
    result = session.cli("stop", ok=False)
    assert path.read_text(encoding="utf-8") == "# private edited unit\n"
    assert session.record.exists()
    assert (session.record.parent / "environment").exists()
    assert "private" not in result.stderr


@pytest.mark.parametrize("artifact", ["helper", "portal"])
def test_dangling_edited_artifacts_retain_ownership_evidence(session: SessionSandbox, artifact: str) -> None:
    session.compositor()
    session.cli("start")
    path = session.units / "dotfiles-sway-helper@waybar.service" if artifact == "helper" else session.dropin
    path.unlink()
    path.symlink_to("private-missing-artifact")
    result = session.cli("stop", ok=False)
    assert result.returncode == 1
    assert path.is_symlink()
    assert session.record.exists()
    assert (session.record.parent / "environment").exists()
    assert "private-missing-artifact" not in result.stderr
