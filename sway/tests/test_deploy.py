"""Integration checks: invoke only the public shell entry point in a sandbox."""
import os
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ENTRY = Path(__file__).resolve().parents[1] / "deploy.sh"


class Deployment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sway-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "checkout"
        self.sway = self.repo / "sway"
        self.sway.mkdir(parents=True)
        for name in ("deploy.sh", "deployment.py"):
            shutil.copy2(ENTRY.parent / name, self.sway / name)
        (self.sway / "config").write_text("untracked i3 reference\n")
        (self.sway / ".private").mkdir(mode=0o700)
        (self.sway / ".private" / "trial-checklist.md").write_text(
            "# Controlled checklist fixture — all cases not tested\n")
        self.home = self.root / "home"
        self.config = self.home / ".config"
        self.config.mkdir(parents=True)
        self.external = self.root / "outside"
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.config), PATH="/usr/bin:/bin")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("pacman", "systemctl"):
            stub = self.bin / name
            stub.write_text("#!/bin/sh\nprintf 'controlled state\\n'\n")
            stub.chmod(0o700)
        self.env["PATH"] = f"{self.bin}:/usr/bin:/bin"

    def cli(self, *args, ok=True):
        result = subprocess.run(["bash", str(self.sway / "deploy.sh"), *map(str, args)],
                                env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def candidate(self):
        source = self.sway / "configuration"
        source.mkdir()
        (source / "config").write_text("# future reviewed Sway configuration\n")
        return source

    def prepare(self):
        result = self.cli("prepare", "--external", self.external)
        return Path(result.stdout.strip())

    def test_refuses_reference_and_requires_explicit_deployment(self):
        self.cli("prepare", "--external", self.external, ok=False)
        self.candidate()
        run = self.prepare()
        self.cli("deploy", run, ok=False)
        self.assertFalse((self.config / "sway").exists())

    def test_verified_dual_backup_and_targeted_symlink_reversal(self):
        source = self.candidate()
        old = self.root / "old-sway"
        old.mkdir()
        (old / "config").write_text("original config\n")
        target = self.config / "sway"
        target.symlink_to("../..//old-sway")
        unrelated = self.config / "hypr"
        unrelated.mkdir()
        (unrelated / "config").write_text("untouched Hyprland\n")
        run = self.prepare()
        mirror = self.external / run.name
        self.cli("verify", run)
        self.cli("verify", mirror)
        manifest = json.loads((run / "manifest.json").read_text())
        prior = manifest["nodes"][manifest["roots"]["target"]]
        self.assertEqual(prior["link"], "../..//old-sway")
        self.assertIsNotNone(prior["target"])
        self.assertEqual(run.stat().st_mode & 0o777, 0o700)
        self.assertEqual((run / "manifest.json").stat().st_mode & 0o777, 0o600)
        self.cli("deploy", run, "--apply")
        self.assertEqual(target.resolve(), source)
        self.cli("reverse", run, "--apply")
        self.assertEqual(os.readlink(target), "../..//old-sway")
        self.assertEqual((target / "config").read_text(), "original config\n")
        self.assertEqual((unrelated / "config").read_text(), "untouched Hyprland\n")
        state = json.loads((run / "deployment.json").read_text())
        self.assertEqual(state["package_changes"], [])
        self.assertEqual(state["service_changes"], [])
        self.assertIn("controlled state", state["prior_state"]["packages"]["stdout"])

    def test_partial_deployment_can_restore_original_directory(self):
        self.candidate()
        target = self.config / "sway"
        target.mkdir()
        (target / "config").write_text("keep this directory\n")
        run = self.prepare()
        stub = self.bin / "ln"
        stub.write_text("#!/bin/sh\nexit 19\n")
        stub.chmod(0o700)
        self.cli("deploy", run, "--apply", ok=False)
        self.assertFalse(target.exists())
        self.cli("reverse", run, "--apply")
        self.assertEqual((target / "config").read_text(), "keep this directory\n")

    def test_failed_backup_and_corruption_never_change_target(self):
        self.candidate()
        target = self.config / "sway"
        target.write_text("original\n")
        self.external.write_text("not a directory")
        self.cli("prepare", "--external", self.external, ok=False)
        self.external.unlink()
        run = self.prepare()
        payload = next((self.external / run.name / "payload").iterdir())
        payload.write_text("corrupt")
        self.cli("deploy", run, "--apply", ok=False)
        self.assertEqual(target.read_text(), "original\n")

    def test_changed_source_and_post_deploy_user_work_are_preserved(self):
        source = self.candidate()
        target = self.config / "sway"
        run = self.prepare()
        (source / "config").write_text("edited after snapshot\n")
        self.cli("deploy", run, "--apply", ok=False)
        self.assertFalse(target.exists())
        run = self.prepare()
        self.cli("deploy", run, "--apply")
        target.unlink()
        target.write_text("new user work\n")
        self.cli("reverse", run, "--apply", ok=False)
        self.assertEqual(target.read_text(), "new user work\n")

    def test_restore_export_is_isolated_and_never_overwrites(self):
        self.candidate()
        old = self.root / "actual"
        old.write_text("behind link\n")
        (self.config / "sway").symlink_to(old)
        run = self.prepare()
        export = self.root / "restore"
        self.cli("verify", run, "--restore-to", export)
        manifest = json.loads((run / "manifest.json").read_text())
        link = export / manifest["roots"]["target"]
        self.assertTrue(link.is_symlink())
        self.assertTrue(link.resolve().is_relative_to(export))
        self.assertEqual(link.read_text(), "behind link\n")
        self.cli("verify", run, "--restore-to", export, ok=False)
        self.assertEqual(old.read_text(), "behind link\n")

    def test_reverse_handles_failed_deployment_before_first_mutation(self):
        self.candidate()
        target = self.config / "sway"
        target.write_text("still original\n")
        run = self.prepare()
        self.config.chmod(0o500)
        try:
            self.cli("deploy", run, "--apply", ok=False)
        finally:
            self.config.chmod(0o700)
        self.cli("reverse", run, "--apply")
        self.assertEqual(target.read_text(), "still original\n")

    def test_changed_configuration_home_is_refused(self):
        self.candidate()
        run = self.prepare()
        self.config.rename(self.home / "saved-config")
        self.config.mkdir()
        self.cli("deploy", run, "--apply", ok=False)
        self.assertFalse((self.config / "sway").exists())

    def test_snapshot_preserves_intermediate_symlink_hops(self):
        self.candidate()
        actual = self.root / "actual"
        actual.write_text("old config\n")
        intermediate = self.root / "intermediate"
        intermediate.symlink_to("actual")
        (self.config / "sway").symlink_to(intermediate)
        run = self.prepare()
        manifest = json.loads((run / "manifest.json").read_text())
        first = manifest["nodes"][manifest["roots"]["target"]]
        second = manifest["nodes"][first["target"]]
        self.assertEqual(second["kind"], "link")
        self.assertEqual(second["link"], "actual")
        other = self.root / "identical"
        other.write_text("old config\n")
        intermediate.unlink()
        intermediate.symlink_to(other)
        self.cli("deploy", run, "--apply", ok=False)

    def test_symlinked_ancestor_is_refused_instead_of_omitted(self):
        self.candidate()
        actual = self.root / "actual-directory"
        actual.mkdir()
        (actual / "config").write_text("old config\n")
        alias = self.root / "alias-directory"
        alias.symlink_to(actual)
        target = self.config / "sway"
        target.symlink_to(alias / "config")
        self.cli("prepare", "--external", self.external, ok=False)
        self.assertEqual(os.readlink(target), str(alias / "config"))
        self.assertEqual((actual / "config").read_text(), "old config\n")

    def test_parent_traversal_cannot_hide_a_symlinked_ancestor(self):
        self.candidate()
        nested = self.root / "nested"
        (nested / "directory").mkdir(parents=True)
        (nested / "config").write_text("actual live contents\n")
        (self.root / "config").write_text("wrong lexical contents\n")
        alias = self.root / "alias"
        alias.symlink_to(nested / "directory")
        target = self.config / "sway"
        target.symlink_to(alias / ".." / "config")
        self.assertEqual(target.read_text(), "actual live contents\n")
        self.cli("prepare", "--external", self.external, ok=False)
        self.assertEqual(target.read_text(), "actual live contents\n")

    def test_reversal_handles_internal_absolute_symlinks_and_detects_edits(self):
        self.candidate()
        target = self.config / "sway"
        target.mkdir()
        (target / "config").write_text("prior config\n")
        (target / "alias").symlink_to(target / "config")
        run = self.prepare()
        self.cli("deploy", run, "--apply")
        state = json.loads((run / "deployment.json").read_text())
        saved = Path(state["displaced"]) / "config"
        saved.write_text("a real later edit\n")
        self.cli("reverse", run, "--apply", ok=False)
        self.assertEqual(saved.read_text(), "a real later edit\n")
        saved.write_text("prior config\n")
        self.cli("reverse", run, "--apply")
        self.assertEqual((target / "alias").read_text(), "prior config\n")
        self.assertEqual(os.readlink(target / "alias"), str(target / "config"))


if __name__ == "__main__":
    unittest.main()
