# Sway preparation and recovery

This is **not a functioning Sway desktop**. `config`, `rofi/`, and `scripts/`
are preserved, untracked i3/X11 work references. Do not install or publish them
as a Sway implementation. The authoritative contract is issue #55 and the
resolution of #52; #56 prepares recovery only.

Nothing here installs/removes packages, changes services, selects a session,
or edits Hyprland or shared helper configuration. Live deployment, installation,
session changes, reboot, and disruptive tests each require separate approval.
Do not run `setup-dotfiles.sh` or the Hyprland installer for this procedure.

## Private preparation

Requirements: Bash, GNU `readlink`/`ln`, Python 3.9+, and (only to initialize
the checklist) authenticated `gh` access to the issue tracker. `pacman` and
`systemctl` are queried read-only during preparation; missing/failed queries
are recorded, not mistaken for successful state capture.

First, initialize the detailed local checklist from the current authoritative
issues. Use an owned, mode-0700 external directory **outside this checkout**:

```sh
bash sway/deploy.sh checklist --external "$HOME/.local/state/dotfiles-sway"
```

This creates `sway/.private/trial-checklist.md` and an external copy. It refuses
to replace either existing checklist. Keep results, device identities, versions,
topologies, reproduction details, regression invalidations, fixes and related
retests private. Every required subcase must pass; unavailable/not-tested cases
block everyday cutover. Optional applications, screen sharing, layout extras and
effects are not blockers. Use harmless sentinels, never actual secrets. Update
the external checklist copy when recording new evidence.

Before editing any existing reference/configuration, preserve it privately.
The implementation of #56 already saved and verified the five original reference
files in timestamped `sway/.private/reference-*` and external copies. Those
backups are private local artifacts, not part of this commit. Preserve them.
Do not edit through an existing config symlink: that edits its destination,
which may be in the checkout.

A later implementation must put its reviewed, Sway-specific configuration in
`sway/configuration/config`, with helper configuration explicitly selected from
that tree. This deployment tool deliberately refuses the old reference. It
links **only** `$XDG_CONFIG_HOME/sway` (default `$HOME/.config/sway`); it does not
overwrite global Waybar, portal, notification, clipboard, or Hyprland settings.
Create/review the real configuration directory beforehand. A symlinked
configuration home is refused. Future additional deployment targets need their
own explicit backup/restore design; do not expand this into the general installer.

After the future candidate exists, prepare **before changing deployment**:

```sh
bash sway/deploy.sh prepare --external "$HOME/.local/state/dotfiles-sway"
# Save the printed timestamped snapshot path as SNAPSHOT.
bash sway/deploy.sh verify "$SNAPSHOT"
bash sway/deploy.sh verify "$EXTERNAL_SNAPSHOT"
```

Preparation captures the existing reference, candidate, affected Sway path, exact
symlink text, and actual files behind links. It records hashes, modes, package
versions, service state, and a deployment journal. Directories are private (0700),
records/payloads are private (0600). Both timestamped copies are restored into
isolated temporary destinations and checked before deployment is possible.
Every direct symlink hop is captured. Special files, cycles, symlinked ancestor
directories, and common secret/clipboard paths are refused rather than silently
omitted; they require a separate backup decision. This is **not** a universal
secret classifier: inspect affected
trees first; do not point it at a home directory or credential/history store.
Preparation failure leaves originals unchanged and may retain an incomplete
snapshot for diagnosis; never deploy from it.

The external copy protects against checkout loss. **Two copies on the same disk
do not protect against disk failure.** Use separately managed encrypted/off-disk
backup if that protection is needed; do not routinely back up clipboard data.

## Explicit deployment and targeted reversal

Only after separate authorization, verified recovery, and review of the candidate:

```sh
bash sway/deploy.sh deploy "$SNAPSHOT" --apply
```

Both verified copies must be available. Candidate and prior target must still
match the snapshot. The prior Sway path is renamed to a timestamped hidden sibling
in the configuration directory; a new symlink points to `sway/configuration`.
The write-ahead journal is copied outside the checkout before mutation.
No packages or services are introduced; their change lists are explicitly empty.
Do not install or remove dependencies under cover of this command.

To reverse only this deployment (including a failed link creation after the old
path was moved):

```sh
bash sway/deploy.sh reverse "$SNAPSHOT" --apply
```

The introduced link is removed only if it still points exactly where recorded.
The saved original is moved back only if it and its referents are unchanged.
An absent prior path is restored as absent. Later user changes cause refusal,
not overwriting. Review the private journal and resolve conflicts manually.
Keep snapshots and displaced originals; do not delete recovery evidence.
Run one deployment/reversal command at a time; stop configuration editors during
preparation/deployment. This tool does not claim transactional safety against
concurrent outside writers or power loss.

If the checkout is lost, use the external snapshot with a trusted copy of
`deploy.sh` and `deployment.py`. Verification and reversal use the recorded paths;
deployment requires the original checkout location.

For inspection or manual recovery without overwriting anything:

```sh
bash sway/deploy.sh verify "$EXTERNAL_SNAPSHOT" --restore-to "$NEW_PRIVATE_DESTINATION"
```

The destination must not exist. `manifest.json` maps `roots` and numbered `nodes`
to their original paths, modes, exact link text and captured referents. The
restored numbered objects contain copied files and **rewritten links to those
copies**, not live originals. Dangling links point to isolated missing objects.
For manual restoration, review the manifest and copy only the affected object to
a new staging path first; recreate the original link text only after validating
its destination. Do not copy an isolated rewritten link into live configuration.
Do not overwrite changed underlying files automatically. If package/service
changes are later separately authorized, record their exact before/after state
and introduced changes privately; reverse only those changes after checking
shared dependencies. Never remove Hyprland or shared dependencies automatically.

## Before the first Sway login

These are **human checks**, not claims of tested behavior:

1. Get separate authorization for the trial. Check `systemctl is-active gdm`
   read-only and inspect installed session entries under
   `/usr/share/wayland-sessions/`. Confirm both the intended Sway entry and
   Hyprland exist; later verify both are actually selectable in GDM.
2. Save work. Switch to an available text console using the machine's verified
   Ctrl+Alt+Fn combination. Log in successfully, confirm the intended account and
   recovery tools, then return to the existing graphical session using its actual
   VT. Record the working combinations privately. Do not guess that a console
   route works; resolve any failure before trying Sway.
3. Log out normally and explicitly choose Sway in GDM. Do not enable autologin or
   force a default. Keep Hyprland installed and selectable. Switching means
   logging out of one desktop before entering the other.
4. Test explicit Sway → Hyprland → Sway return, desktop activation environment,
   portals, authentication, helper ownership and cleanup. Separate config files
   alone do not isolate the shared D-Bus/systemd user environment.

## An unresponsive Sway session

Stopping a session **can lose unsaved work**. Prefer normal logout if possible.
Use the already-tested console route and log in. Identify sessions first:

```sh
loginctl list-sessions
loginctl show-session SESSION_ID -p Name -p User -p Type -p Desktop -p State -p Leader -p TTY
loginctl session-status SESSION_ID
```

Inspect the selected session's process tree/cgroup and leader. Confirm its owner,
Wayland/Sway identity, and actual failed compositor. `Desktop` may be missing;
do not infer the session solely from that field or take the first matching user.
Exclude the console recovery session, GDM greeter, Hyprland, and unrelated sessions.
If the failed Sway session cannot be identified unambiguously, stop and investigate.

Only after explicit confirmation, if needed:

```sh
loginctl terminate-session CONFIRMED_FAILED_SWAY_SESSION_ID
```

Return to the verified GDM VT and choose Hyprland. Never routinely restart GDM,
terminate the whole user, run `killall`/`pkill -u`, or kill shared portal/helpers
indiscriminately. If GDM or Hyprland is unavailable, remain in the console and
diagnose; do not compound the failure with broad process killing. Restore only
affected Sway paths if needed, using the targeted procedure above.

Everyday Sway requires all required checklist cases to pass. Passing is not
authorization to remove Hyprland: that also needs a verified reboot/fallback and
separate approval. Essential regressions invalidate affected passes and block
removal until fixed and retested. The user decides whether to continue or return
to Hyprland; disable unsafe features in the meantime.

## Isolated checks

```sh
python3 -m unittest discover -s sway/tests -v
python3 -m py_compile sway/deployment.py sway/tests/test_deploy.py
bash -n sway/deploy.sh
```

Tests run the public command in temporary checkouts/homes with controlled
package/service queries and link-creation failure. They do not contact the live
desktop, clipboard, devices, or services. They do not prove real hardware,
locking, session switching, portal behavior, or a successful Sway trial.
