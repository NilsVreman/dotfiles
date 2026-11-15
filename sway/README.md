# Sway preparation and recovery

`configuration/` is the **minimal, untried standard-Sway candidate** from #57, not the complete desktop from #55.
`config`, `rofi/`, and `scripts/` remain preserved, untracked i3/X11 references: do not install or publish them.
The authoritative contract is #55 and the resolution of #52; #56 supplies verified deployment/recovery, not evidence of a successful real-machine trial.

Merely checking out this tree installs no packages, changes no services, and selects no session.
Live deployment, installation, session changes, reboot, and disruptive tests each require separate approval.
Do not run `setup-dotfiles.sh` or the Hyprland installer for this procedure.

## Private preparation

Requirements are Bash, GNU `readlink`/`ln`, **Python 3.12 or newer**, and authenticated `gh` access only when initializing the checklist.
Both Python programs use the standard library and existing external commands; deployment, recovery, and session startup require neither uv nor an installed Python package.
`pacman` and `systemctl` are queried read-only during preparation; missing or failed queries are recorded rather than mistaken for successful state capture.

First initialize the detailed local checklist from the current authoritative issues.
Use an owned, mode-0700 external directory **outside this checkout**:

```sh
bash sway/deploy.sh checklist --external "$HOME/.local/state/dotfiles-sway"
```

This prints the new `sway/.private/trial-checklist.md` path and creates an external copy.
It refuses to replace either existing checklist.
Keep results, device identities, versions, topologies, reproduction details, regression invalidations, fixes, and related retests private.
Every required subcase must pass; unavailable or not-tested cases block everyday cutover.
Optional applications, screen sharing, layout extras, and effects are not blockers.
Use harmless sentinels, never actual secrets, and update the external copy when recording evidence.

Before editing any existing reference or configuration, preserve it privately.
The implementation of #56 already saved and verified the five original reference files in timestamped private `reference-*` snapshots and external copies.
Those backups are private local artifacts, not version-controlled; preserve them.
Do not edit through an existing configuration symlink without reviewing its destination: that may edit the checkout.

The reviewed candidate is `sway/configuration/config`, with helper configuration and styles explicitly selected from that tree.
The deployment tool refuses the old reference and links **only** `$XDG_CONFIG_HOME/sway`, defaulting to `$HOME/.config/sway`.
It does not overwrite global Waybar, portal, notification, clipboard, or Hyprland settings.
Review the candidate and authentication ownership first.
A symlinked configuration home is refused.
Additional targets require their own explicit backup/restore design rather than an expansion of the general installer.

After review, prepare before changing deployment:

```sh
bash sway/deploy.sh prepare --external "$HOME/.local/state/dotfiles-sway"
# Save the printed timestamped snapshot path as SNAPSHOT.
bash sway/deploy.sh verify "$SNAPSHOT"
bash sway/deploy.sh verify "$EXTERNAL_SNAPSHOT"
```

Preparation captures the references, candidate, affected Sway path, exact symlink text, and actual files behind links.
It records hashes, modes, package versions, service state, and a deployment journal.
Directories are private (0700) and records/payloads are private (0600).
Both timestamped copies are restored into isolated temporary destinations and checked before deployment is possible.
Verification prints `Snapshot integrity and isolated restoration verified.` on success.
Every direct symlink hop is captured.
Special files, cycles, symlinked ancestors, and common secret/clipboard paths require a separate backup decision and are refused rather than silently omitted.
This is **not** a universal secret classifier: review affected trees first and do not point preparation at a home directory or credential/history store.
Preparation failure leaves originals unchanged and may retain an incomplete snapshot for diagnosis; never deploy from it.

The external copy protects against checkout loss, but **two copies on the same disk do not protect against disk failure**.
Use separately managed encrypted or off-disk backup if needed; do not routinely copy clipboard data.

## Explicit deployment and targeted reversal

Only after separate authorization, verified recovery, and candidate review, apply the prepared link:

```sh
bash sway/deploy.sh deploy "$SNAPSHOT" --apply
```

Both verified copies must be available, and the candidate and prior target must still match the snapshot.
The old Sway path is renamed to a timestamped hidden sibling in the configuration directory; a new symlink points to `sway/configuration`.
The write-ahead journal is copied outside the checkout before mutation.
Success reports that only the Sway configuration link was deployed.
No packages or services are introduced; their change lists are explicitly empty.
Do not install or remove dependencies under cover of this command.

Reverse only the recorded deployment, including failed link creation after the prior path was moved:

```sh
bash sway/deploy.sh reverse "$SNAPSHOT" --apply
```

The introduced link is removed only if it still points exactly where recorded.
The saved original is moved back only if it and its referents are unchanged.
An absent prior path is restored as absent.
Success reports restoration of only the prior Sway path, or that it was already intact without mutation.
Later user changes cause refusal rather than overwriting.
Review the private journal and resolve conflicts manually.
Keep snapshots and displaced originals as recovery evidence.
Run one deployment/reversal command at a time and stop configuration editors during preparation/deployment.
The tool does not claim transactional safety against concurrent outside writers or power loss.

If the checkout is lost, use the external snapshot with trusted adjacent copies of `deploy.sh` and `deployment.py`.
Verification and reversal use the recorded paths; deployment requires the original checkout location.
Valid pre-refactor snapshots, journals, and ownership records remain usable without migration.
Additional unknown record fields are not themselves a reason for refusal.

For inspection or manual recovery without overwriting anything, export to a new private destination:

```sh
bash sway/deploy.sh verify "$EXTERNAL_SNAPSHOT" --restore-to "$NEW_PRIVATE_DESTINATION"
```

The destination must not exist.
`manifest.json` maps `roots` and numbered `nodes` to original paths, modes, exact link text, and captured referents.
The restored numbered objects contain copied files and **rewritten links to those copies**, not live originals.
Dangling links point to isolated missing objects.
For manual restoration, review the manifest and copy only the affected object to a new staging path first.
Recreate original link text only after validating its destination; do not install an isolated rewritten link into live configuration.
Never automatically overwrite changed underlying files.
If package/service changes are separately authorized later, privately record exact before/after state and introduced changes and reverse only those changes after checking shared dependencies.
Never remove Hyprland or shared dependencies automatically.

## Before the first Sway login

These are **human checks**, not claims of tested behavior.

1. Obtain separate trial authorization.
   Query `systemctl is-active gdm` read-only and inspect `/usr/share/wayland-sessions/`.
   Confirm both entries exist and later verify both are selectable in GDM.
2. Save work and switch to an available text console using the machine's verified Ctrl+Alt+Fn combination.
   Log in successfully, confirm the intended account and recovery tools, and return to the graphical session using its actual VT.
   Record working combinations privately; resolve any failed console route before trying Sway.
3. Log out normally and explicitly choose Sway in GDM.
   Do not enable autologin or force a default, and keep Hyprland installed and selectable.
   Switching means logging out of one desktop before entering the other.
4. Test Sway → Hyprland → Sway return, activation environment, portals, authentication, helper ownership, and cleanup.
   Separate files alone do not isolate the shared D-Bus/systemd user environment.

**Do not attempt the first login until both backups/isolated restoration, console login/return, and the available Hyprland GDM fallback are verified.**
Record the actual Sway entry's filename, `Exec`, `DesktopNames`, selection, and login/logout results privately.
A file on disk is not a passing GDM check.
Use the distribution's standard Sway entry rather than replacing Hyprland's; this repository installs no entry.

## Minimal session ownership (#57)

See [the architecture](docs/architecture.md) for implementation details and extending helper ownership.
Copy the sanitized [session trial template](session-trial.template.md) to a **new** mode-0600 private file and an external private backup, preserving existing checklist results.
Every case starts **not tested**.

The authorized machine needs standard Sway/Swaymsg, systemd's user manager, `dbus-update-activation-environment`, `busctl`, procps `ps`, Waybar, swaync, swaybg, NetworkManager's applet, the selected polkit agent, Wofi, Wlogout, Kitty, and the wlr/GTK/Hyprland portal providers in addition to the runtime requirements above.
Dependencies are **not installed here**.
Check actual versions, service availability, and command support during authorized preparation.
A missing portal unit or failed inventory aborts startup rather than guessing.

`configuration/session.json` enables Waybar, swaync, a solid-color swaybg, and `nm-applet --indicator`.
The applet uses existing NetworkManager rather than starting a second daemon.
Wofi and Wlogout use explicit Sway files/styles.
Only logout is offered in this initial power menu.
Locking, suspend policy, Kanshi, dashboards, wallpaper assets, clipboard capture, and its writers belong to later tickets.
**This base alone is not safe for everyday cutover.**

Authentication has exactly one selected owner:

- Default `"authentication": {"owner": "session"}` starts polkit-gnome in an owned cgroup.
  It conservatively refuses recognized existing processes, installed user-agent services even when disabled, active system agents, and advertised D-Bus peers.
  It never disables, masks, replaces, or stops those owners.
- For an existing active service, select `{"owner": "external", "unit": "ACTUAL-AGENT.service", "scope": "user"}`.
  Use `"scope": "system"` to check an existing system service instead.
- For an already acquired user D-Bus name, select `{"owner": "external", "bus_name": "ACTUAL.AGENT.NAME"}` instead of a unit.
  Checking does not activate the name, and external owners are never cleaned up by Sway.

Replace examples with the inventoried owner; service/name existence is **not** proof of polkit registration.
Inventory cannot recognize every integrated agent or prevent an unrelated concurrent launch.
Resolve unfamiliar owners explicitly and verify prompts/cancellation privately in **both** desktops.
Do not add another autostart agent or an agent-replacement flag.

From an authorized Sway login, startup runs once through:

```sh
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/session.py" start
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/session.py" status
```

Super+Shift+r reloads only Sway configuration.
Repeated `start` reports existing ownership without restarting active helpers or portals, and refuses another owning compositor.
A new session's successful start reports that helpers started under their session target.
`status` prints JSON containing `active`, `socket`, `helpers`, and selected desktop `environment` keys.
It reports service activity, **not readiness** of UI, portals, or authentication; keep actual output private.
Helper definitions and policy changes apply to a subsequent session rather than redefining the current owner's helpers.
Status, repeated start, stop, and cleanup use recorded ownership even if a helper's current definition is changed or removed.

On logout, IPC loss, or guard failure, the target stops helper cgroups before activation-environment finalization.
From the verified console, request an idempotent helper stop:

```sh
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/session.py" stop
```

Success reports that only owned helpers stopped; this does not terminate the compositor or session.
Follow targeted recovery below for a frozen compositor.
No command stops `graphical-session.target`, PipeWire, the polkit authority, or unrelated services.
Incomplete or inconsistent cleanup retains its ownership record and recovery evidence and blocks a new owner.
If a helper lacks matching recorded unit evidence, the command refuses without issuing guessed stop requests or substituting current configuration.
Edited runtime unit files and unverifiable owned processes retain their safeguards and evidence.
An edited artifact that is now a dangling symlink also causes cleanup refusal and evidence retention.
Inspect the journal rather than deleting the record to force a login.

### Desktop activation and the Hyprland return route

Only logout/login switching is supported, **not concurrent same-user graphical sessions**.
Sway refreshes explicit desktop/display/IPC keys in both activation environments, clearing stale Hyprland identity.
A runtime drop-in changes **only the portal frontend's** configuration home to `configuration/portals/`.
This pins Sway ScreenCast/Screenshot to wlr with GTK fallback even if the installed Hyprland portal advertises Sway.
The paired Hyprland preference file explicitly selects Hyprland with GTK fallback.
Global portal and helper files remain untouched.

Transitions stop/join available named frontend/wlr/GTK/Hyprland brokers, including pending activations, and start the selected providers after separately updating D-Bus and verifying systemd's environment.
These shared brokers are not owned helper cgroups; stopping them can interrupt portal requests.
Transitions therefore belong to logout/login rather than arbitrary reload.
Verify actual provider use and new display connections; static preference files and active units are not proof.

The live Hyprland tree is symlinked into this checkout and remains **unchanged**.
After an authorized logout to Hyprland, run this in its terminal:

```sh
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/session.py" refresh-hyprland
```

This refuses incomplete Sway cleanup, refreshes Hyprland display/desktop values, empties Sway IPC identifiers, selects Hyprland/GTK portals, and leaves helper/authentication startup alone.
Success reports refreshed Hyprland activation environment and explicit providers.
**Until the opt-in hook is deployed, run this on every Hyprland return before testing portal applications.**

`configuration/hyprland-session.conf` is an optional login fragment, not sourced or deployed automatically.
Adding a `source` line to live Hyprland requires separate authorization, verified path/link/referent backups, and a private change/reversal record.
The link tool backs up and reverses only Sway deployment, not that optional edit.
Remove a recorded source line before reversing the Sway link.
Manual refresh avoids editing Hyprland and is the initial trial route.

Cleanup verifies empty owned cgroups before removing unchanged runtime artifacts and clearing only its own complete activation identity.
It never restores stale display sockets; failed half-import clearing is retained as failed recovery evidence.
Hyprland refresh leaves the paired runtime portal override until the next Sway cleanup or user-runtime teardown, not as a persistent installed override.
After checkout/link loss, do not restart portals against a missing candidate: use the console and verified recovery record.
Hyprland and its original configuration remain independently available.

## Errors and retained evidence

Malformed configuration, snapshots, journals, and ownership records produce controlled refusals rather than tracebacks or guessed recovery actions.
Commands exit 0 on success, 1 on a handled runtime failure, and 2 on command-line usage errors.
Runtime errors begin with `Refused/failed:` for deployment or `Sway session refused/failed:` for session control.
Error messages omit offending values, including paths, helper names, subprocess arguments, and raw OS/subprocess output.
This does not redact intentional successful status/path output or change private recovery-record formats.

After a refusal, inspect preserved evidence privately and resolve the cause before retrying.
Malformed recovery or ownership input is not permission to overwrite configuration or discard records.

## An unresponsive Sway session

Stopping a session **can lose unsaved work**; prefer normal logout when possible.
Use the already-tested console route and identify sessions first:

```sh
loginctl list-sessions
loginctl show-session SESSION_ID -p Name -p User -p Type -p Desktop -p State -p Leader -p TTY
loginctl session-status SESSION_ID
```

Inspect the selected session's process tree/cgroup and leader and confirm its owner, Wayland/Sway identity, and failed compositor.
`Desktop` may be missing; do not infer ownership solely from it or take the first session for the user.
Exclude the console, GDM greeter, Hyprland, and unrelated sessions.
If identification is ambiguous, stop and investigate.

Only after explicit confirmation, if needed, terminate that failed session:

```sh
loginctl terminate-session CONFIRMED_FAILED_SWAY_SESSION_ID
```

Return to the verified GDM VT and choose Hyprland.
Never routinely restart GDM, terminate the whole user, run `killall`/`pkill -u`, or kill shared services indiscriminately.
If GDM or Hyprland is unavailable, remain in the console and diagnose rather than escalating to broad process killing.
Restore only affected Sway paths using targeted reversal.

Everyday Sway requires every required checklist case to pass.
Passing does not authorize Hyprland removal, which also needs verified reboot/fallback and separate approval.
Essential regressions invalidate affected passes and block removal until fixed and retested.
The user decides whether to continue or return to Hyprland; disable unsafe features meanwhile.

## Isolated checks

The supported development test runner is pytest with the locked uv environment.
From the repository root, run the full isolated suite and optional static shell/unit checks:

```sh
uv run --project sway --locked pytest sway/tests
bash -n sway/deploy.sh
sh -n sway/configuration/scripts/menu.sh
systemd-analyze --user verify sway/configuration/systemd/*
```

See [DEVELOPING.md](DEVELOPING.md) for linting, strict typing, interpreter selection, and optional scoped hooks.
Tests use temporary checkouts/homes, controlled package/service/D-Bus queries, a private IPC peer, harmless pre-refactor fixtures, and injected failures.
They never contact the live desktop, clipboard, devices, or services, and hook tests install hooks only in disposable repositories.
They do not prove real hardware, locking, systemd lifecycle, session switching, portals, authentication, or a successful trial.
