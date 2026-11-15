# Private #57 session trial — all results NOT TESTED

Copy to a new mode-0600 file under `sway/.private/` and to the private external
backup. Do not replace existing checklist evidence. This sanitized template is
public; filled-in results, actual commands/paths, hardware and session details
stay private. Supplement the authoritative #55/#52 checklist, do not replace it.

Authorization/date: NOT GRANTED
Versions/builds/topology: NOT RECORDED
Everyday cutover: BLOCKED
Hyprland removal: NOT AUTHORIZED

For **each subcase**, record pass / fail / not tested; required missing evidence
blocks cutover. Record steps, expected/actual result, relevant unit/process/cgroup
identity, timing, and related retests after any fix. No real credentials or
clipboard contents. Do not run controlled failures without separate approval.

| Required case | Status | Private evidence / reproduction / retest |
| --- | --- | --- |
| Verified local AND external snapshots; hashes and isolated restoration succeed; affected links/referents recorded | not tested | |
| Successful console login AND return to actual graphical VT; tools/account confirmed | not tested | |
| Actual Sway and Hyprland session-entry paths/Exec/DesktopNames and GDM selections; fallback available BEFORE first Sway login | not tested | |
| Standard Sway login and normal Wlogout logout; return to GDM; login again | not tested | |
| Each enabled helper/authentication agent has one owner and cgroup; exact Sway config/style arguments, no global Hyprland helper configuration | not tested | |
| Repeated start and multiple Super+Shift+r reloads preserve helper and guard PIDs/start times; no duplicate processes or portal restart | not tested | |
| Normal logout leaves no owned helpers, watcher children or in-flight writers; unrelated pre-existing service remains active with same identity | not tested | |
| Authorized controlled compositor failure closes IPC; guard loss stops target, helper cgroups and finalizer within documented bounds; unrelated service survives | not tested | |
| Authorized guard failure ALSO tears down the target; no session auto-restart; console recovery stops ONLY the identified failed Sway session | not tested | |
| Authorized partial-start failure unwinds introduced resources; failed cleanup is reported/retained, cannot be bypassed by silently starting another owner | not tested | |
| Sway D-Bus AND systemd activation have current desktop/type/display/Sway sockets, no stale Hyprland identity; fresh activated client reaches current display | not tested | |
| Sway actual portal frontend uses wlr ScreenCast/Screenshot and GTK fallback interfaces, NOT installed Hyprland provider despite UseIn advertising Sway | not tested | |
| Actual polkit request and cancellation use exactly the chosen agent; missing/external agent policy is honest; no competing system/D-Bus/autostart agent | not tested | |
| Sway → logout → Hyprland: manual refresh or separately backed-up opt-in hook; correct new activation display/desktop/type, empty Sway identifiers, Hyprland/GTK provider use | not tested | |
| Hyprland fallback helpers, authentication prompts/cancellation and ordinary applications still work; no duplicate agents or Sway processes | not tested | |
| Hyprland → logout → Sway: fresh ownership, environment, providers and authentication work again; no leaked Hyprland helper interferes | not tested | |
| When later enabled, repeat reload/logout/failure cleanup for swayidle, Kanshi, clipboard watchers AND child writers as well as Waybar/swaync/swaybg/NM applet/owned auth agent | not tested | |

Use only an approved harmless authentication operation that actually requires an
agent; record success/cancellation without passwords. An active service or
acquired bus name is not evidence of a working registered agent.

Inspect the relevant user units' `MainPID`, `ControlGroup`, `ActiveState`,
`SubState`, `Result` and journals before/after. Track an existing unrelated benign
service; never create a disruptive sentinel or stop shared services as a shortcut.
Validate that cgroups contain no child writers after stop, not merely that the
parent PID exited. Future clipboard tests use harmless sentinels only.

For controlled failure, save work and confirm the exact selected compositor or
guard first. No user-wide signals, no stopping `graphical-session.target`, no
GDM restart. Use the verified console and README's session-identification checks.
If cleanup/fallback cannot be demonstrated, stop the trial and retain fail/not
tested; static tests do not override that result.
