# Maintaining the Sway code

## Map and interfaces

| Path | Responsibility |
| --- | --- |
| `deploy.sh` → `deployment.py` | Private snapshots, verification, and one reversible Sway directory link. Never desktop/service/package control. |
| `configuration/config` | Minimal native Sway controls and a single `exec … session.py start`. No distro/global autostart includes. |
| `configuration/scripts/session.py` | Session control interface: `start`, `stop`, `status`, `refresh-hyprland`. Also implements internal systemd commands `guard` and `cleanup`. |
| `configuration/systemd/` | Lifetime/dependency ordering and bounded helper cgroup cleanup. Runtime-linked, never enabled globally. |
| `configuration/session.json` | Enabled helpers and one authentication owner. Changes take effect on the next login, not Sway reload. |
| `configuration/helpers.json` | Exact argument arrays for foreground helpers. `@CONFIG@` expands to this candidate's resolved directory, not a shell fragment. |
| `configuration/portals/` | Explicit desktop-specific provider selection for the shared portal frontend. |
| `configuration/{waybar,swaync,wofi,wlogout}/`, `styles/` | Sway-only helper configurations/styles. No dependency on Hyprland integration. |
| `tests/` | Public-command integration checks with external-command substitutes and real private IPC sockets. |
| `.private/` | Git-ignored backups, actual trial results and machine details. Never publish. |
| `config`, `rofi/`, `scripts/` | Original untracked i3/X11 references. Not implementation inputs, not overwritten. |

All Python code uses the standard library. Shell is limited to entry-point/menu
adapters. Read [README.md](README.md) before running any live operation. Changing
a symlink target in the repository can change live configuration: **do not edit
Hyprland or an already deployed candidate without separate authorization**.

## Session lifetime and failure ordering

`start` validates a standard-Sway IPC peer with GET_VERSION, serializes ownership
requests with a runtime lock, and refuses a different compositor or incomplete
prior cleanup. Before mutations it checks authentication ownership, unowned helper
processes, required portal units, and conflicting runtime overrides.

Only `$XDG_RUNTIME_DIR/dotfiles-sway-session/` contains our session state:

- `session.json`: owning socket, selected helpers, stopping flag, exact runtime
  helper-unit texts, explicit environment and its previous desktop keys.
  No credentials, clipboard data or arbitrary environment.
- `environment`: private systemd `EnvironmentFile` with this login's display/IPC
  values and the exact configuration directory.
- `lock`: serializes `start`, `refresh-hyprland`, and finalization.

Lifecycle unit files are linked using `systemctl --user link --runtime` without
force. Helpers get runtime instance files rendered from the shared template:
their executable paths are checked first, and `ExecStart` runs the tool directly,
not a Python/shell launcher. This lets `Type=exec` detect the tool's exec failure.
Files have no `[Install]`/automatic login enablement; edited runtime files are
preserved, and unchanged owned instance files are removed after verified cleanup.
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

The guard reports READY only after the IPC subscription acknowledgement.
Normal shutdown, EOF/reset after a crash, and guard failure all deactivate it;
the target's `BindsTo` then tears down the owned helpers. A hung compositor with
an open socket requires the documented console recovery; this is not a custom
compositor watchdog.

**Stop order is the reverse**: helpers → target → guard → cleanup. Do not move
environment cleanup into the guard's `ExecStopPost`: on abrupt guard exit it
could run before dependent helper cgroups have stopped. The separate finalizer
preserves ordering even on failure.

Each helper uses `KillMode=control-group`, TERM followed by KILL after
`TimeoutStopSec=5`, and no restart policy. This covers child watchers/writers
that remain in that cgroup, including a shell pipeline's children. Do not daemonize,
fork a new systemd scope, or put a writer in another service without equivalent
ownership. Guard start/stop is bounded to 10 seconds; the finalizer has 60 seconds.
Individual control-plane commands time out at 20 seconds; the explicit helper
stop allows up to 90 seconds for the ordered transaction. Failure is reported
and recovery state retained, not called a completed cleanup.

`stop` requests only recorded helper instances and the three lifecycle units.
It first waits for startup's lock, records a stopping flag, then releases the lock
before waiting for systemd: the finalizer must not deadlock on its caller.
Otherwise a stop could finish before startup had even created its units.
Startup releases its lock **before** invoking synchronous failure
cleanup. The finalizer takes the lock so it cannot finish while startup is still
importing a dying compositor's environment. `cleanup` is idempotent and also handles partial startup.
Do not invoke the internal hook while helpers are active; use `stop`.

Before clearing ownership, cleanup checks helper/guard state, main/control PIDs
and descendant task accounting. A remaining populated or unverifiable cgroup
retains the ownership record and blocks another login owner, even if systemd's
stop job itself succeeded. No escalation beyond the owned cgroup is attempted.

Reload executes neither startup nor helper restart. A second `start` for the
same healthy target is a no-op; a failed helper is reported rather than silently
called a healthy session. It is not an automatic repair of a crashed helper.
Inspect `status` and the relevant user journal, then explicitly start an affected
owned helper if appropriate during the authorized trial. Service activity is not
proof of GUI or authentication readiness.

## Activation and ownership

D-Bus activation and the systemd user manager outlive graphical logins.
`import_environment` sends only the listed desktop/display/IPC keys to both,
including empty values for the previous desktop's identifiers; it never imports
the whole shell environment. D-Bus and systemd updates are separate checked
calls: `dbus-update-activation-environment --systemd` can warn and still exit 0
when its manager update failed. We verify systemd's values through JSON output,
which preserves spaces/quotes, and clear the D-Bus half-import on failure even
if the manager still has its previous values. Failed clearing retains evidence.
Cleanup compares the **whole** desktop identity, not just a potentially inherited
Sway socket, before clearing values. We do **not** restore old, dead Hyprland
sockets. A delayed cleanup must not overwrite a newer desktop.

`portal_override` uses one named **runtime** drop-in for
`xdg-desktop-portal.service`, setting its `XDG_CONFIG_HOME` to our portal-only
configuration root. This leaves ordinary applications, helpers, and the user's
global configuration home untouched. Both desktop-specific preference files are
present; no `*` provider fallback can accidentally pick Hyprland for Sway.
Required units and conflicting/symlinked override paths are checked before
transition. An edited override is preserved, not forcibly replaced/removed.

Only named portal brokers are stopped on transitions. No PipeWire, WirePlumber,
keyring, network daemon, authority, global graphical target, or unrelated service
is stopped. Provider selection requires an actual new frontend process; just
updating activation environment does not change already-running brokers.
Synchronous stops include available named brokers which are still activating
or deactivating; `is-active` alone would miss those old jobs. Real same-user
concurrent graphical sessions are deliberately unsupported.

Authentication selection never uses a replacement flag or stops an existing
owner. The default conservative inventory can produce a refusal even for a
disabled installed agent: choose an explicit verified external owner or resolve
that inventory under separate authorization. No heuristic proves registration;
the private real-session prompt/cancellation cases remain mandatory.

## Adding a later helper

1. Add its explicit Sway argument array to `helpers.json`, and its configuration
   and styles under this candidate. Share only genuinely compositor-neutral
   assets. No implicit global helper defaults or Hyprland command calls.
2. Add the helper name to `session.json` only when its ticket's safety checks
   permit startup. The existing template gives it one cgroup and session lifetime;
   no extra `exec`, `exec_always`, XDG autostart, or global user-service enablement.
3. Keep it foregrounded. Swayidle, Kanshi, clipboard capture **and in-flight
   writers** must remain within owned cgroups. Do not enable clipboard history
   before its separate privacy/version/storage checks.
4. If a dashboard needs start/stop control (e.g. Kanshi), operate on its exact
   `dotfiles-sway-helper@NAME.service`. Never `pkill`, `killall`, or restart every
   helper. Fresh-login policy belongs in session startup, not persistent flags.
5. Extend the confirmed public-command test seam with that behavior and add private
   real-session cleanup cases. Cgroup escapes, hardware behavior, authentication,
   portal use and lock readiness cannot be proven by substitutes.

## Snapshot/reversal implementation

`Snapshot.capture` treats files, directories and symlinks as a graph. Every link
hop retains its exact text and points to a separately captured referent.
An active recursion set rejects cycles; shared paths reuse IDs. It rejects
special files, symlinked ancestors and known sensitive paths rather than producing
an incomplete, apparently successful backup. This is not a secret classifier.

`verify` checks manifest/payload integrity and reconstructs the graph in an
isolated temporary directory. Restored links point at copied objects, never live
originals; those rewritten links are for verification/export, not installation.
`unchanged` compares reachable content/modes/link graphs independently of IDs.
Relocation maps internal absolute links when checking the displaced original.

Both snapshot copies and the candidate/prior target must verify before deployment.
`deployment.json` records intent in both copies **before** the rename/link. Its
phase distinguishes an untouched target, an interrupted deployment, a deployed
link and an interrupted reversal. Reversal refuses later edits or a replaced
configuration home rather than overwriting them. The tool is deliberately not
transactional against outside writers or power loss and does not roll back
unrecorded edits, installations, optional Hyprland hooks or service changes.

## Checks and evidence

Run individual test files while changing their interface, then the full suite
once at the end; commands are in README.md. For optional type checking with an
already available mypy:

```sh
mypy --check-untyped-defs sway/deployment.py sway/configuration/scripts sway/tests
```

Tests never use the real bus, live clipboard, devices or user manager.
`systemd-analyze --user verify` checks unit syntax/dependencies offline; it does
not execute the lifecycle. The [trial template](session-trial.template.md) records
that missing evidence explicitly. No static check is a passed GDM, portal,
authentication, reload or cgroup-cleanup trial.

Primary references used for this design:
[Sway systemd integration](https://github.com/swaywm/sway/wiki/systemd-integration),
[systemd.unit](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html),
[systemd.kill](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html),
[portal configuration](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html).
