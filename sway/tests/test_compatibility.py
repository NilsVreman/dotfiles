"""Recover pre-refactor records without migration or access to private data."""

import shutil
import subprocess
from pathlib import Path

import pytest
from helpers import (
    DeploymentSandbox,
    SessionSandbox,
    load_fixture,
    read_link,
    read_record,
    write_manifest,
    write_record,
)


@pytest.mark.parametrize("has_extra_fields", [False, True])
def test_trusted_pair_alone_verifies_and_reverses_a_pre_refactor_snapshot(
    deployment: DeploymentSandbox, has_extra_fields: bool
) -> None:
    fixture = load_fixture("deployment-v1.json", deployment.root)
    manifest, journal = fixture["manifest"], fixture["journal"]
    journal["config_identity"] = [deployment.config.stat().st_dev, deployment.config.stat().st_ino]
    if has_extra_fields:
        manifest["future_metadata"] = {"version": 2}
        journal["future_metadata"] = {"keep": "unchanged"}
        for node in manifest["nodes"].values():
            node["future_metadata"] = True
    old = deployment.root / "old-sway"
    old.write_text("legacy original\n", encoding="utf-8")
    old.chmod(0o644)
    target = deployment.config / "sway"
    target.symlink_to(journal["source"])
    Path(journal["displaced"]).symlink_to(old)
    run = Path(journal["external"])
    run.mkdir(parents=True, mode=0o700)
    write_manifest(run, manifest)
    write_record(run / "deployment.json", journal)
    payload = run / "payload"
    payload.mkdir(mode=0o700)
    for key, text in fixture["payload"].items():
        (payload / key).write_text(text, encoding="utf-8")
    trusted = deployment.root / "trusted"
    trusted.mkdir()
    for name in ("deploy.sh", "deployment.py"):
        shutil.copy2(deployment.sway / name, trusted / name)
    # Remove only this test-created checkout, not any user work.
    shutil.rmtree(deployment.repo)
    for arguments in (["verify", str(run)], ["reverse", str(run), "--apply"]):
        result = subprocess.run(
            ["/bin/bash", str(trusted / "deploy.sh"), *arguments],
            env=deployment.env,
            text=True,
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr
    assert read_link(target) == str(old)
    assert target.read_text(encoding="utf-8") == "legacy original\n"
    recovered = read_record(run / "deployment.json")
    assert recovered["phase"] == "reversed"
    if has_extra_fields:
        assert recovered["future_metadata"] == {"keep": "unchanged"}


@pytest.mark.parametrize("has_extra_fields", [False, True])
@pytest.mark.parametrize("helper_name", ["waybar", "waybar:secondary", r"waybar\x2dsecondary", "waybar@secondary"])
def test_pre_refactor_session_record_remains_owned_until_verified_cleanup(
    session: SessionSandbox, has_extra_fields: bool, helper_name: str
) -> None:
    session.compositor()
    state = load_fixture("session-v1.json", session.root)
    state["helpers"] = [helper_name if name == "waybar" else name for name in state["helpers"]]
    state["unit_files"][f"dotfiles-sway-helper@{helper_name}.service"] = state["unit_files"].pop(
        "dotfiles-sway-helper@waybar.service"
    )
    if has_extra_fields:
        state["future_metadata"] = {"keep": "unchanged"}
    session.record.parent.mkdir(mode=0o700)
    write_record(session.record, state)
    (session.record.parent / "environment").write_text("# legacy environment\n", encoding="utf-8")
    session.units.mkdir(parents=True)
    for unit, text in state["unit_files"].items():
        (session.units / unit).write_text(text, encoding="utf-8")
    manager = {
        "units": {
            "unrelated.service": "active",
            "dotfiles-sway-session.target": "active",
            "dotfiles-sway-guard.service": "active",
            "dotfiles-sway-cleanup.service": "active",
            **dict.fromkeys(state["unit_files"], "active"),
        },
        "environment": {key: value for key, value in state["environment"].items() if key != "DOTFILES_SWAY_CONFIG"},
    }
    write_record(Path(session.env["FAKE_MANAGER"]), manager)
    write_record(session.config / "helpers.json", {})
    assert set(session.status()["helpers"]) == set(state["helpers"])
    session.cli("start")
    assert session.record.exists()
    session.cli("stop", ok=False, env=dict(session.env, SURVIVING_HELPER=helper_name))
    if has_extra_fields:
        assert read_record(session.record)["future_metadata"] == {"keep": "unchanged"}
    session.cli("stop")
    assert not session.record.exists()
    assert all(not (session.units / unit).exists() for unit in state["unit_files"])
    assert session.status()["helpers"] == {}
