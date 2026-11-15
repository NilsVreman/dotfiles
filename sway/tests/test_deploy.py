"""Invoke only the public shell entry point in an isolated deployment sandbox."""

from pathlib import Path

from helpers import DeploymentSandbox, read_link, read_record, script, write_manifest


def test_refuses_reference_and_requires_explicit_deployment(deployment: DeploymentSandbox) -> None:
    deployment.cli("prepare", "--external", deployment.external, ok=False)
    deployment.candidate()
    run = deployment.prepare()
    deployment.cli("deploy", run, ok=False)
    assert not (deployment.config / "sway").exists()


def test_verified_dual_backup_and_targeted_symlink_reversal(deployment: DeploymentSandbox) -> None:
    source = deployment.candidate()
    old = deployment.root / "old-sway"
    old.mkdir()
    (old / "config").write_text("original config\n", encoding="utf-8")
    target = deployment.config / "sway"
    target.symlink_to("../..//old-sway")
    unrelated = deployment.config / "hypr"
    unrelated.mkdir()
    (unrelated / "config").write_text("untouched Hyprland\n", encoding="utf-8")
    run = deployment.prepare()
    deployment.cli("verify", run)
    deployment.cli("verify", deployment.external / run.name)
    manifest = read_record(run / "manifest.json")
    prior = manifest["nodes"][manifest["roots"]["target"]]
    assert prior["link"] == "../..//old-sway"
    assert prior["target"] is not None
    assert run.stat().st_mode & 0o777 == 0o700
    assert (run / "manifest.json").stat().st_mode & 0o777 == 0o600
    deployment.cli("deploy", run, "--apply")
    assert target.resolve() == source
    deployment.cli("reverse", run, "--apply")
    assert read_link(target) == "../..//old-sway"
    assert (target / "config").read_text(encoding="utf-8") == "original config\n"
    assert (unrelated / "config").read_text(encoding="utf-8") == "untouched Hyprland\n"
    state = read_record(run / "deployment.json")
    assert state["package_changes"] == []
    assert state["service_changes"] == []
    assert "controlled state" in state["prior_state"]["packages"]["stdout"]


def test_partial_deployment_can_restore_original_directory(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.mkdir()
    (target / "config").write_text("keep this directory\n", encoding="utf-8")
    run = deployment.prepare()
    (deployment.bin / "ln").unlink()
    script(deployment.bin / "ln", "#!/bin/sh\nexit 19\n")
    deployment.cli("deploy", run, "--apply", ok=False)
    assert not target.exists()
    deployment.cli("reverse", run, "--apply")
    assert (target / "config").read_text(encoding="utf-8") == "keep this directory\n"


def test_failed_backup_and_corruption_never_change_target(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.write_text("original\n", encoding="utf-8")
    deployment.external.write_text("not a directory", encoding="utf-8")
    deployment.cli("prepare", "--external", deployment.external, ok=False)
    deployment.external.unlink()
    run = deployment.prepare()
    payload = next((deployment.external / run.name / "payload").iterdir())
    payload.write_text("corrupt", encoding="utf-8")
    deployment.cli("deploy", run, "--apply", ok=False)
    assert target.read_text(encoding="utf-8") == "original\n"


def test_malformed_manifest_is_a_sanitized_refusal_without_live_changes(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.write_text("original\n", encoding="utf-8")
    run = deployment.prepare()
    write_manifest(run, ["offending-private-manifest"])
    evidence = (run / "manifest.json").read_bytes()
    result = deployment.cli("reverse", run, "--apply", ok=False)
    assert "Traceback" not in result.stderr
    assert "offending-private-manifest" not in result.stderr
    assert result.stderr.startswith("Refused/failed:")
    assert target.read_text(encoding="utf-8") == "original\n"
    assert (run / "manifest.json").read_bytes() == evidence


def test_changed_source_and_post_deploy_user_work_are_preserved(deployment: DeploymentSandbox) -> None:
    source = deployment.candidate()
    target = deployment.config / "sway"
    run = deployment.prepare()
    (source / "config").write_text("edited after snapshot\n", encoding="utf-8")
    deployment.cli("deploy", run, "--apply", ok=False)
    assert not target.exists()
    run = deployment.prepare()
    deployment.cli("deploy", run, "--apply")
    target.unlink()
    target.write_text("new user work\n", encoding="utf-8")
    deployment.cli("reverse", run, "--apply", ok=False)
    assert target.read_text(encoding="utf-8") == "new user work\n"


def test_restore_export_is_isolated_and_never_overwrites(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    old = deployment.root / "actual"
    old.write_text("behind link\n", encoding="utf-8")
    (deployment.config / "sway").symlink_to(old)
    run = deployment.prepare()
    export = deployment.root / "restore"
    deployment.cli("verify", run, "--restore-to", export)
    manifest = read_record(run / "manifest.json")
    link = export / manifest["roots"]["target"]
    assert link.is_symlink()
    assert link.resolve().is_relative_to(export)
    assert link.read_text(encoding="utf-8") == "behind link\n"
    deployment.cli("verify", run, "--restore-to", export, ok=False)
    assert old.read_text(encoding="utf-8") == "behind link\n"


def test_reverse_handles_failed_deployment_before_first_mutation(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.write_text("still original\n", encoding="utf-8")
    run = deployment.prepare()
    deployment.config.chmod(0o500)
    try:
        deployment.cli("deploy", run, "--apply", ok=False)
    finally:
        deployment.config.chmod(0o700)
    deployment.cli("reverse", run, "--apply")
    assert target.read_text(encoding="utf-8") == "still original\n"


def test_changed_configuration_home_is_refused(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    run = deployment.prepare()
    deployment.config.rename(deployment.home / "saved-config")
    deployment.config.mkdir()
    deployment.cli("deploy", run, "--apply", ok=False)
    assert not (deployment.config / "sway").exists()


def test_snapshot_preserves_intermediate_symlink_hops(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    actual = deployment.root / "actual"
    actual.write_text("old config\n", encoding="utf-8")
    intermediate = deployment.root / "intermediate"
    intermediate.symlink_to("actual")
    (deployment.config / "sway").symlink_to(intermediate)
    run = deployment.prepare()
    manifest = read_record(run / "manifest.json")
    first = manifest["nodes"][manifest["roots"]["target"]]
    second = manifest["nodes"][first["target"]]
    assert second["kind"] == "link"
    assert second["link"] == "actual"
    other = deployment.root / "identical"
    other.write_text("old config\n", encoding="utf-8")
    intermediate.unlink()
    intermediate.symlink_to(other)
    deployment.cli("deploy", run, "--apply", ok=False)


def test_symlinked_ancestor_is_refused_instead_of_omitted(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    actual = deployment.root / "actual-directory"
    actual.mkdir()
    (actual / "config").write_text("old config\n", encoding="utf-8")
    alias = deployment.root / "alias-directory"
    alias.symlink_to(actual)
    target = deployment.config / "sway"
    target.symlink_to(alias / "config")
    deployment.cli("prepare", "--external", deployment.external, ok=False)
    assert read_link(target) == str(alias / "config")
    assert (actual / "config").read_text(encoding="utf-8") == "old config\n"


def test_parent_traversal_cannot_hide_a_symlinked_ancestor(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    nested = deployment.root / "nested"
    (nested / "directory").mkdir(parents=True)
    (nested / "config").write_text("actual live contents\n", encoding="utf-8")
    (deployment.root / "config").write_text("wrong lexical contents\n", encoding="utf-8")
    alias = deployment.root / "alias"
    alias.symlink_to(nested / "directory")
    target = deployment.config / "sway"
    target.symlink_to(alias / ".." / "config")
    assert target.read_text(encoding="utf-8") == "actual live contents\n"
    deployment.cli("prepare", "--external", deployment.external, ok=False)
    assert target.read_text(encoding="utf-8") == "actual live contents\n"


def test_reversal_handles_internal_absolute_symlinks_and_detects_edits(deployment: DeploymentSandbox) -> None:
    deployment.candidate()
    target = deployment.config / "sway"
    target.mkdir()
    (target / "config").write_text("prior config\n", encoding="utf-8")
    (target / "alias").symlink_to(target / "config")
    run = deployment.prepare()
    deployment.cli("deploy", run, "--apply")
    saved = Path(read_record(run / "deployment.json")["displaced"]) / "config"
    saved.write_text("a real later edit\n", encoding="utf-8")
    deployment.cli("reverse", run, "--apply", ok=False)
    assert saved.read_text(encoding="utf-8") == "a real later edit\n"
    saved.write_text("prior config\n", encoding="utf-8")
    deployment.cli("reverse", run, "--apply")
    assert (target / "alias").read_text(encoding="utf-8") == "prior config\n"
    assert read_link(target / "alias") == str(target / "config")
