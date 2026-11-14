"""Verified snapshots and narrow Sway symlink deployment, not a desktop installer.

Public interface: deploy.sh. Recovery instructions: README.md. The snapshot graph,
write-ahead journal, and refusal rules are explained in DEVELOPING.md. No function
here installs packages, changes services, or controls the graphical session.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile


SWAY = Path(__file__).resolve().parent
REPO = SWAY.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def present(path):
    return os.path.lexists(path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    """Replace one private record atomically; callers coordinate the two copies."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.chmod(0o600)
    os.replace(temporary, path)


def private_dir(path):
    """Create private storage, but never silently chmod an existing user directory."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    require(not path.is_symlink() and path.stat().st_uid == os.getuid(),
            f"Not an owned private directory: {path}")
    require(stat.S_IMODE(path.stat().st_mode) == 0o700,
            f"Directory must already have mode 0700: {path}")


class Snapshot:
    """Capture paths as a graph so exact link text AND each referent survive.

    IDs refer to payload objects, not original paths. Active recursion detects
    cycles; seen paths allow shared referents. Relocation is used only to compare
    a displaced original during reversal, including absolute links inside it.
    """
    def __init__(self, directory, relocation=None):
        self.directory = directory
        self.relocation = relocation
        self.nodes = {}
        self.seen = {}
        self.active = set()

    def capture(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if self.relocation:
            original, displaced = self.relocation
            if path.is_relative_to(original):
                path = displaced / path.relative_to(original)
        require(not any(parent.is_symlink() for parent in path.parents),
                f"Symlinked ancestor needs separate backup review: {path}")
        # Only collapse '..' after checking the literal path's ancestors.
        # alias/../file follows alias first on the real filesystem.
        path = Path(os.path.abspath(path))
        require(path not in self.active, f"Symlink cycle: {path}")
        if path in self.seen:
            return self.seen[path]
        if not present(path):
            return None
        # Refuse rather than silently omit sensitive data from an affected tree.
        require(path.name.lower() not in {
            ".private", ".ssh", ".gnupg", "cliphist", "cliphist-sway",
            "secrets", "credentials", "db",
        } and path.suffix.lower() not in {".key", ".pem", ".kdbx"},
                f"Sensitive/private path requires a separate backup decision: {path}")
        key = str(len(self.nodes))
        self.seen[path] = key
        info = path.lstat()
        node = {"path": str(path), "mode": stat.S_IMODE(info.st_mode)}
        self.nodes[key] = node
        self.active.add(path)
        if path.is_symlink():
            link_text = os.readlink(path)
            node.update(kind="link", link=link_text)
            # Follow one hop, not resolve(): every intermediate link is evidence.
            link_target = Path(link_text)
            if not link_target.is_absolute():
                link_target = path.parent / link_target
            node["target"] = self.capture(link_target)
        elif path.is_dir():
            node.update(kind="directory", children={
                child.name: self.capture(child) for child in sorted(path.iterdir())
            })
        else:
            require(stat.S_ISREG(info.st_mode), f"Not a regular file: {path}")
            data = path.read_bytes()
            node.update(kind="file", sha256=digest(data))
            payload = self.directory / "payload" / key
            payload.parent.mkdir(exist_ok=True, mode=0o700)
            payload.write_bytes(data)
            payload.chmod(0o600)
        self.active.remove(path)
        return key


def isolated_restore(run, manifest, destination):
    """Reconstruct links against copied referents, never against live originals."""
    destination.mkdir(mode=0o700)
    nodes = manifest["nodes"]

    def restore(key, path):
        node = nodes[key]
        if node["kind"] == "file":
            data = (run / "payload" / key).read_bytes()
            require(digest(data) == node["sha256"], f"Corrupt payload: {key}")
            path.write_bytes(data)
            path.chmod(node["mode"])
        elif node["kind"] == "directory":
            path.mkdir(mode=0o700)
            for name, child in node["children"].items():
                restore(child, path / name)
        else:
            target = destination / (node["target"] if node["target"] is not None
                                    else f"missing-{key}")
            path.symlink_to(os.path.relpath(target, path.parent))

    for key in nodes:
        restore(key, destination / key)
    for key, node in nodes.items():
        path = destination / key
        if node["kind"] == "link":
            if node["target"] is not None:
                require(path.resolve() == (destination / node["target"]).resolve(),
                        "Isolated symlink restoration failed")
        elif node["kind"] == "file":
            require(digest(path.read_bytes()) == node["sha256"], "Restore mismatch")


def load(run):
    """Check snapshot ownership and manifest integrity before trusting its graph."""
    require(run.is_dir() and not run.is_symlink(), "Snapshot directory missing")
    require(run.stat().st_uid == os.getuid()
            and stat.S_IMODE(run.stat().st_mode) == 0o700,
            "Snapshot directory must be owned and mode 0700")
    data = (run / "manifest.json").read_bytes()
    require(digest(data) == (run / "manifest.sha256").read_text().strip(),
            "Manifest integrity check failed")
    return json.loads(data)


def verify(run):
    """Reconstruct and verify in isolation; never restore onto live originals."""
    manifest = load(run)
    with tempfile.TemporaryDirectory(prefix="restore-", dir=run) as temporary:
        isolated_restore(run, manifest, Path(temporary) / "objects")
    return manifest


def query(command):
    """Record read-only inventory honestly, including unavailable/failed queries."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        return {"command": command, "returncode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": command, "unavailable": str(error)}


def journal(run, state):
    # Intent is durable in both copies before any link mutation.
    for copy in (run, Path(state["external"])):
        write_json(copy / "deployment.json", state)


def backup_root(external):
    """Require a second private location outside the checkout, not just another path."""
    external = external.expanduser().absolute()
    require(not external.resolve().is_relative_to(REPO),
            "External backup must be outside checkout")
    private_dir(external)
    private_dir(SWAY / ".private")
    return external


def checklist(external):
    """Keep issue text, actual topology and all results out of version control."""
    external = backup_root(external)
    destination = SWAY / ".private" / "trial-checklist.md"
    require(not present(destination) and not present(external / destination.name),
            "Checklist already exists; preserve results and update manually")
    sources = {}
    for number in (55, 52):
        result = subprocess.run(
            ["gh", "issue", "view", str(number), "--repo", "NilsVreman/dotfiles",
             "--json", "number,title,body,comments"],
            capture_output=True, text=True, check=True, timeout=60)
        sources[number] = json.loads(result.stdout)
    resolution = "\n".join(comment["body"] for comment in sources[52]["comments"]
                           if "## Resolution" in comment["body"])
    require(resolution, "Issue #52 resolution missing")
    text = [
        "# Private Sway trial — not deployment evidence",
        "",
        "Sources: #55 and #52 resolution. All required cases block cutover until pass.",
        "Optional application/effect/layout results do not block cutover.",
        "No real credentials or clipboard contents. Use harmless sentinels.",
        "Same-disk backups do not protect against disk failure.",
        "",
        "Trial authorization/date: NOT GRANTED",
        "Actual tool versions/build options: NOT RECORDED",
        "Actual device identities, modes, topology, lid/dock state: NOT RECORDED",
        "Console login/return, GDM and Hyprland availability: not tested",
        "Everyday cutover: BLOCKED; Hyprland removal: NOT AUTHORIZED",
        "",
        "For each case use pass / fail / not tested. Split compound cases into",
        "subcases as needed; every required subcase must pass. Missing devices",
        "remain not tested. Optional cases stay optional. Regressions invalidate",
        "affected passes; record related cases and retest after fixes. NilsVreman",
        "chooses whether to continue or return to Hyprland; no automatic rollback.",
        "",
    ]
    for label, body in (("#55", sources[55]["body"]), ("#52 resolution", resolution)):
        section = ""
        cases = []
        for line in body.splitlines():
            if line.startswith("#"):
                section = line.lstrip("# ")
            elif (re.match(r"^(?:\d+\. |- )", line)
                  or (line.startswith("  | ") and "---" not in line
                      and "Keys" not in line)):
                cases.append((section, line.strip()))
            elif line.startswith("  ") and cases and line.strip():
                previous_section, previous = cases[-1]
                cases[-1] = (previous_section, previous + "\n" + line)
        for index, (section, requirement) in enumerate(cases, 1):
            text.extend([
                f"## {label} case {index}: {section}", "",
                requirement, "",
                "- Status: not tested",
                "- Required/optional: follow source (never promote optional checks)",
                "- Versions/builds and topology:",
                "- Reproduction steps / harmless inputs:",
                "- Expected / actual / evidence (no clipboard content):",
                "- Regression / invalidated previous result / related cases:",
                "- Fix / retest date / retest result:",
                "",
            ])
        text.extend([f"# Authoritative source: {label}", "", body, ""])
    destination.write_text("\n".join(text))
    destination.chmod(0o600)
    mirror = external / destination.name
    shutil.copyfile(destination, mirror)
    mirror.chmod(0o600)
    require(destination.read_bytes() == mirror.read_bytes(), "Checklist copies differ")
    print(destination)


def prepare(external):
    """Snapshot candidate, reference, target and referents; verify BOTH copies.

    Capture and isolated restore are prerequisites, not evidence of a working
    desktop. Any failure keeps the live target unchanged and retains diagnostics.
    """
    source = SWAY / "configuration"
    require(source.is_dir() and not source.is_symlink()
            and (source / "config").is_file(),
            "No reviewed sway/configuration/config; refusing the i3 work reference")
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    require(config.is_absolute() and config.is_dir() and not config.is_symlink(),
            "Create/review a real absolute XDG_CONFIG_HOME before preparation")
    config = config.resolve()
    require(not config.is_relative_to(REPO), "Configuration home must be outside checkout")
    external = backup_root(external)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run = SWAY / ".private" / stamp
    run.mkdir(mode=0o700)
    mirror = external / stamp
    try:
        snapshot = Snapshot(run)
        roots = {name: snapshot.capture(path) for name, path in {
            "reference-config": SWAY / "config",
            "reference-rofi": SWAY / "rofi",
            "reference-scripts": SWAY / "scripts",
            "source": source,
            "target": config / "sway",
        }.items()}
        manifest = {"roots": roots, "nodes": snapshot.nodes}
        write_json(run / "manifest.json", manifest)
        (run / "manifest.sha256").write_text(digest((run / "manifest.json").read_bytes()) + "\n")
        state = {
            "source": str(source), "target": str(config / "sway"),
            "config_identity": [config.stat().st_dev, config.stat().st_ino],
            "displaced": str(config / f".sway.before-{stamp}"),
            "external": str(mirror), "phase": "prepared",
            "package_changes": [], "service_changes": [],
            "prior_state": {
                "packages": query(["pacman", "-Q"]),
                "system_services": query(["systemctl", "list-unit-files", "--no-pager"]),
                "user_services": query(["systemctl", "--user", "list-unit-files", "--no-pager"]),
                "active_system_services": query(["systemctl", "list-units", "--all", "--no-pager"]),
                "active_user_services": query(["systemctl", "--user", "list-units",
                                               "--all", "--no-pager"]),
                "gdm": query(["systemctl", "is-active", "gdm"]),
            },
        }
        write_json(run / "deployment.json", state)
        checklist_path = SWAY / ".private" / "trial-checklist.md"
        require(checklist_path.is_file(), "Initialize the private checklist first")
        shutil.copyfile(checklist_path, run / "trial-checklist.md")
        verify(run)
        shutil.copytree(run, mirror, symlinks=True)
        mirror.chmod(0o700)
        verify(mirror)
        require((mirror / "manifest.json").read_bytes()
                == (run / "manifest.json").read_bytes(), "Backup copies differ")
    except Exception:
        # Keep incomplete evidence; no target has been changed.
        raise
    print(run)


def unchanged(run, manifest, roots, relocation=None):
    """Compare reachable content/link graphs rather than capture-specific node IDs."""
    with tempfile.TemporaryDirectory(prefix="compare-", dir=run) as temporary:
        snapshot = Snapshot(Path(temporary), relocation)
        current = {name: snapshot.capture(Path(path)) for name, path in roots.items()}
        # Compare only the reachable subgraph: IDs can differ across captures.
        def tree(nodes, key):
            if key is None:
                return None
            node = dict(nodes[key])
            node.pop("path")
            if node["kind"] == "directory":
                node["children"] = {name: tree(nodes, child)
                                    for name, child in node["children"].items()}
            elif node["kind"] == "link":
                node["target"] = tree(nodes, node["target"])
            return node
        for name, key in current.items():
            require(tree(snapshot.nodes, key) == tree(manifest["nodes"], manifest["roots"][name]),
                    f"{name} changed after snapshot; prepare again")


def deploy(run, authorized):
    """Journal intent in both locations before renaming the single affected path."""
    require(authorized, "Deployment requires --apply and separate live-machine authorization")
    manifest = verify(run)
    state = json.loads((run / "deployment.json").read_text())
    require(state["phase"] == "prepared", "Snapshot has already been used")
    mirror = Path(state["external"])
    require(verify(mirror) == manifest, "External backup differs")
    require(json.loads((mirror / "deployment.json").read_text()) == state,
            "Deployment records differ")
    require(state["source"] == str(SWAY / "configuration"),
            "Use the deployment entry point from the original checkout")
    unchanged(run, manifest, {"source": state["source"], "target": state["target"]})
    target, displaced = Path(state["target"]), Path(state["displaced"])
    check_config_identity(target.parent, state)
    require(not present(displaced), "Displacement path already exists")
    state["phase"] = "deploy-intent"
    journal(run, state)
    if present(target):
        target.rename(displaced)
    # If this fails, reverse can recover from deploy-intent and the saved original.
    subprocess.run(["ln", "-sT", "--", state["source"], str(target)], check=True)
    state["phase"] = "deployed"
    journal(run, state)
    print("Deployed only the Sway configuration link; no packages/services changed.")


def reverse(run, authorized):
    """Undo only our recorded link/rename, refusing later edits or ambiguous state.

    Intent phases make interrupted renames retryable. This is not a transaction
    against concurrent outside writers, and does not reverse package/service work.
    """
    require(authorized, "Reversal requires --apply")
    manifest = verify(run)
    state = json.loads((run / "deployment.json").read_text())
    require(state["phase"] in {"deploy-intent", "deployed", "reverse-intent"},
            "No introduced deployment to reverse")
    target, displaced = Path(state["target"]), Path(state["displaced"])
    check_config_identity(target.parent, state)
    if (state["phase"] in {"deploy-intent", "reverse-intent"}
            and not present(displaced) and manifest["roots"]["target"] is not None):
        # A failed rename, or a completed restoration interrupted before journaling.
        unchanged(run, manifest, {"target": str(target)})
        state["phase"] = "reversed"
        journal(run, state)
        print("Original Sway path is already intact; no mutation needed.")
        return
    require(not present(target) or
            (target.is_symlink() and os.readlink(target) == state["source"]),
            "Target changed since deployment; refusing to overwrite user work")
    if manifest["roots"]["target"] is not None:
        require(present(displaced), "Prior object missing; use verified backup for manual recovery")
        unchanged(run, manifest, {"target": str(displaced)},
                  relocation=(target, displaced))
    else:
        require(not present(displaced), "Unexpected displaced object")
    state["phase"] = "reverse-intent"
    journal(run, state)
    if present(target):
        target.unlink()
    if present(displaced):
        displaced.rename(target)
    state["phase"] = "reversed"
    journal(run, state)
    print("Restored only the prior Sway path; packages/services and shared dependencies untouched.")


def check_config_identity(config, state):
    """Do not mutate a replacement configuration home created after preparation."""
    require(not config.is_symlink()
            and [config.stat().st_dev, config.stat().st_ino] == state["config_identity"],
            "Configuration home changed since snapshot; refusing mutation")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialization = commands.add_parser("checklist")
    initialization.add_argument("--external", required=True, type=Path)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--external", required=True, type=Path)
    for name in ("verify", "deploy", "reverse"):
        command = commands.add_parser(name)
        command.add_argument("snapshot", type=Path)
        if name == "verify":
            command.add_argument("--restore-to", type=Path)
        else:
            command.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.command == "checklist":
        checklist(args.external)
    elif args.command == "prepare":
        prepare(args.external)
    elif args.command == "verify":
        run = args.snapshot.absolute()
        manifest = verify(run)
        if args.restore_to:
            isolated_restore(run, manifest, args.restore_to.absolute())
        print("Snapshot integrity and isolated restoration verified.")
    elif args.command == "deploy":
        deploy(args.snapshot.absolute(), args.apply)
    else:
        reverse(args.snapshot.absolute(), args.apply)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Refused/failed: {error}", file=sys.stderr)
        sys.exit(1)
