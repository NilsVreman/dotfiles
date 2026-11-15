# Sway implementation

The supported interfaces are the commands documented in [README.md](../README.md), not an installed Python package.
Development commands and hook usage live in [DEVELOPING.md](../DEVELOPING.md).

## Code map and execution

| Path under `sway/` | Responsibility |
| --- | --- |
| `deploy.sh` → `deployment.py` | Private snapshots, verification, and one reversible configuration link; no desktop, service, or package control. |
| `configuration/config` | Native Sway controls and a single session-start command, without global autostart includes. |
| `configuration/scripts/session.py` | Session lifecycle, activation environment, portals, authentication inventory, and systemd finalization. |
| `configuration/systemd/` | Dependency ordering and bounded helper cgroup cleanup; runtime-linked, never enabled globally. |
| `configuration/session.json` | Helpers selected for the next session and one authentication owner. |
| `configuration/helpers.json` | Foreground helper argument arrays; `@CONFIG@` expands to the resolved candidate directory, not shell code. |
| `configuration/portals/` | Explicit desktop-specific provider preferences for the shared portal frontend. |
| `configuration/{waybar,swaync,wofi,wlogout}/`, `configuration/styles/` | Explicit Sway-only helper resources. |
| `tests/helpers.py`, `tests/conftest.py` | Isolated homes, environment setup, private IPC peers, and intended test-interpreter selection. |
| `tests/substitutes/command.py` | Typed external-command model, copied into test sandboxes rather than embedded in strings. |
| `tests/fixtures/` | Harmless pre-refactor recovery records with documented provenance and relocatable paths. |
| `config`, `rofi/`, `scripts/` | Preserved untracked i3/X11 references, not maintained implementation. |
| `.private/` | Ignored local recovery and trial evidence, never an input to automated tests. |

Both Python programs remain standard-library-only, using system Python at their existing entry points.
Deployment deliberately has no imports from session code or development helpers: a trusted adjacent `deploy.sh`/`deployment.py` pair must survive checkout loss.
All session implementation and resources remain inside the deployed configuration tree.
The uv project is non-package development tooling with no build backend or runtime dependencies.

## Typed input and error handling

JSON input is narrowed at the input seam into `TypedDict` structures after runtime validation.
The snapshot graph distinguishes files, directories, and links; the deployment journal and session record retain their existing serialized field names and meanings.
Unknown fields are retained when records are rewritten, and snapshot content comparisons use only the defined content/mode/link fields.
Validation rejects wrong container types, absent required fields, invalid references, unsafe object names, cyclic graphs, invalid modes, inconsistent deployment paths, and inconsistent helper ownership.
Graph validation happens before restoration writes and journal validation before configuration mutations.
Session record validation happens before issuing ownership-based stop requests or rewriting recovery evidence.

Controlled refusals carry fixed, value-free messages.
The command dispatchers sanitize decoder, operating-system, and subprocess failures instead of rendering raw exceptions or captured failure output.
The argument parsers similarly replace value-bearing usage messages while retaining usage-error exit behavior.
Private inventory records keep their existing detailed format; sanitization applies to errors, not private recovery data or intentional successful output.
The small duplicated validators are deliberate: sharing them outside either standalone runtime would weaken recovery locality.

## Session lifetime and ordering

`start` validates the standard-Sway IPC peer with GET_VERSION, serializes ownership requests with a runtime lock, and refuses another compositor or incomplete prior cleanup.
Before live mutations it checks authentication ownership, unowned helper processes, required portal providers, and conflicting runtime overrides.
Only `$XDG_RUNTIME_DIR/dotfiles-sway-session/` contains our session state:

- `session.json` records the socket, selected helper names, stopping flag when present, exact runtime helper-unit texts, imported environment, and previous desktop keys.
  It contains no credentials, clipboard data, or unrelated environment.
- `environment` is the private systemd `EnvironmentFile`, pinning this login's display, IPC, and configuration values.
- `lock` serializes startup, Hyprland refresh, stop's ownership snapshot, and finalization.

Lifecycle files are linked with `systemctl --user link --runtime`, without force.
Runtime helper instances are rendered from the shared template after executable validation.
Their direct `ExecStart` executes the tool, not an intermediate Python or shell launcher, so `Type=exec` observes the tool's exec failure.
The files have no `[Install]` section and no automatic login enablement.
Edited runtime files are preserved; unchanged owned instances are removed only after verified cleanup.
The dependency graph is intentionally small:

```text
cleanup.service (oneshot, remains active until stop)
        before
guard.service (Type=notify, shutdown subscription)
        before / BindsTo
session.target
        before / BindsTo / PartOf
helper@NAME.service (one foreground process tree)
```

The guard reports READY only after Sway acknowledges the shutdown subscription.
Normal shutdown, IPC EOF/reset, or guard failure deactivates it; the target's `BindsTo` then tears down helpers.
A hung compositor with an open socket still requires the console recovery procedure; the guard is not a compositor watchdog.
Stop ordering reverses the graph: helpers, target, guard, then cleanup.
Environment cleanup must remain in the separate finalizer, not the guard's `ExecStopPost`, so it cannot run ahead of dependent cgroups.

Each helper uses `KillMode=control-group`, TERM followed by KILL after `TimeoutStopSec=5`, task accounting, and no restart policy.
Child watchers and writers remain owned only while they remain in that cgroup.
Guard start/stop is bounded to 10 seconds, finalization to 60 seconds, ordinary control-plane calls to 20 seconds, and the ordered explicit stop to 90 seconds.
Failure retains recovery evidence rather than claiming completed cleanup.

Stop first waits for startup's lock, snapshots the validated record, writes its stopping flag, and releases the lock before waiting for systemd.
The finalizer also takes that lock; holding it across a synchronous stop would deadlock.
Startup likewise releases its lock before synchronous failure cleanup.
Cleanup is idempotent and handles partial startup.
It checks helper/guard activity, main/control PIDs, and descendant task accounting before clearing ownership.
A surviving populated or unverifiable cgroup retains the record and blocks another login owner.
No escalation beyond the owned cgroup is attempted.

A session-owned helper remains owned until cleanup is verified, independently of later definition changes.
Current policy and helper definitions are consulted only for a new session.
For an existing session, helper names must match the recorded instance-file evidence exactly.
Missing, extra, or invalid unit evidence causes refusal without substituting current definitions or issuing guessed stop requests.
Instance-name validation follows systemd's character set, including colon, backslash escape text, and additional `@` characters, while rejecting unsafe filesystem names.
Cleanup uses `lstat` to distinguish absent artifacts from dangling symlinks and propagates other stat failures rather than treating them as absence.
Repeated start for the same healthy owner is a no-op; failed helpers are reported rather than silently restarted.
Configuration reload invokes neither startup nor helper restart.
Activity is never interpreted as UI or authentication readiness.

## Activation, portals, and authentication

D-Bus activation and the systemd user manager outlive graphical logins.
Environment import sends only explicit desktop/display/IPC keys, including empty values for the previous desktop's identifiers.
It never imports the entire shell environment.
D-Bus and systemd updates are separate checked calls because `dbus-update-activation-environment --systemd` can warn and still exit successfully when the manager update fails.
The manager's JSON mapping preserves spaces and quoting; its unrelated keys never enter status output.
Failed half-imports clear the D-Bus side or retain failure evidence if clearing fails.
Cleanup compares the entire desktop identity, not merely an inherited Sway socket.
It never restores old, dead Hyprland sockets or overwrites a newer desktop's imported identity.

One named runtime drop-in sets only the portal frontend's `XDG_CONFIG_HOME` to the candidate's portal-only tree.
Applications and helpers keep their ordinary configuration home.
Both desktop-specific preference files are present, without a wildcard provider fallback that could select Hyprland for Sway.
Required units and conflicting or symlinked override paths are checked before transitions.
Edited portal overrides are preserved.
Only named portal brokers are stopped, including pending activating/deactivating brokers that `is-active` alone would miss.
No PipeWire, WirePlumber, keyring, network daemon, authority, global graphical target, or unrelated service is stopped.
Provider selection requires a new frontend process; environment changes alone do not reconfigure existing brokers.
Concurrent same-user graphical sessions remain unsupported.

Authentication selection never replaces, masks, or stops another owner.
The default conservative inventory can refuse even disabled installed agent services.
An explicitly selected external service or acquired D-Bus name remains externally owned and is never cleaned up by Sway.
No inventory heuristic proves polkit registration or prevents an unrelated concurrent launch.
Actual prompts and cancellation must still be checked privately in both desktops.

## Adding a later helper

Later helpers inherit the same session ownership rather than adding another startup mechanism.
The helper must stay foregrounded and must not escape into a detached scope or separately owned writer process.

1. Add its explicit argument array to `helpers.json` and its configuration/styles within the candidate.
   Share only genuinely compositor-neutral assets.
2. Enable its name in `session.json` only after its ticket's safety checks permit startup.
   Do not add duplicate `exec`, `exec_always`, XDG autostart, or globally enabled user services.
3. Keep watchers and in-flight writers in the owned cgroup.
   Clipboard collection still requires its separate privacy, version, and storage gates.
4. If a dashboard needs individual control, use that helper's exact instance rather than killing by process name or restarting all helpers.
   Fresh-login policy belongs in startup, not persistent override flags.
5. Extend the confirmed command seam and the private real-session checks.
   Substitutes cannot prove cgroup escapes, hardware behavior, portal use, authentication, or lock readiness.

## Snapshot and reversal

`Snapshot.capture` treats files, directories, and symlinks as a graph.
Every direct link hop retains its exact text and separately captured referent.
An active recursion set rejects cycles while shared paths reuse identifiers.
Special files, symlinked ancestors, and known sensitive paths are refused rather than omitted from an apparently complete backup.
This is not a secret classifier.

Verification checks manifest and payload integrity and reconstructs the graph in an isolated temporary directory.
Restored links point only to copied objects, never live originals.
Those rewritten links are for verification/export rather than installation.
The reachable content/mode/link comparison is independent of capture-specific identifiers.
Displaced-root comparison maps internal absolute links when checking the saved original.

Both copies and the candidate/prior target must verify before deployment.
The write-ahead journal records intent in both copies before rename or link creation.
Its phases distinguish a prepared snapshot, interrupted deployment, deployed link, interrupted reversal, and completed reversal.
Reversal refuses later user edits and replacement configuration homes rather than overwriting them.
The tool is not transactional against outside writers or power loss.
It does not reverse unrecorded edits, installations, optional Hyprland hooks, or service changes.

## Automated evidence

Tests cross the deployment CLI, session CLI, and pre-commit CLI seams.
They use isolated homes, harmless recovery fixtures, a private IPC peer, and controlled external commands rather than the live user bus, desktop, clipboard, devices, or manager.
Hook checks use disposable repositories with staged, unstaged, untracked, outside-Sway, and configuration-only changes.
They also put an unusable uv project at the disposable repository root to detect wrong-project selection.
Ruff receives staged filenames; mypy receives no filenames and runs from the nested project against all maintained code, without writing a project cache.
No test hook or commit-message hook is installed.

Offline unit validation checks only systemd syntax/dependencies.
The [trial template](../session-trial.template.md) records missing real-machine evidence explicitly.
No static check or substitute is a passed GDM, systemd lifecycle, portal, authentication, reload, cgroup, or hardware trial.
Primary design references are [Sway systemd integration](https://github.com/swaywm/sway/wiki/systemd-integration), [systemd.unit](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html), [systemd.kill](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html), and [portal configuration](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html).
