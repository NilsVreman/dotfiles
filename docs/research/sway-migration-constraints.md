# Standard Sway compatibility and migration constraints

Research for [#48](https://github.com/NilsVreman/dotfiles/issues/48), supporting
[migration map #47](https://github.com/NilsVreman/dotfiles/issues/47).
Observed 2026-10-25; repository baseline `17282e3`.

## Bottom line (research, not a target decision)

Standard Sway is a credible i3-like Wayland candidate for the observed Intel
machine. Its documented container layouts, bindings, shell execution, IPC,
output controls and input controls cover the broad desktop capabilities visible
here [S1–S5]. **This is not a successful hardware trial or a promise of fewer
failures.** No Sway session was started, no packages installed, and no desktop
settings changed. Work-i3 configuration and safe-to-share scripts have not been
provided; their bindings, helpers and exact habits cannot yet be evaluated.

The likely benefit is reducing compositor-specific configuration surface and
custom glue, not making Arch update-proof. Most existing generic Wayland tools
can be assessed for retention; Hyprland dispatch/configuration and integration
points must be translated. Optional transparency does not require a fork.

## Evidence and limits

- **Observed** means a read-only command or file inspection on this machine.
- **Documented** means upstream documentation/source; citations below distinguish
  released versions from moving documentation.
- **Inference / untested** means a planning implication, not demonstrated behavior.
- Local facts came from `uname -a`, `/etc/os-release`, `lspci -nnk`, `lsmod`,
  `/dev/dri`, `/sys/class/drm/*/{status,modes}`, selected `pacman -Q` queries,
  `loginctl`, environment variables, `hyprctl version`, `hyprctl monitors -j`,
  `hyprctl devices -j`, process names, configuration files and symlink targets.
  No client titles, clipboard contents, screenshots or credentials were collected.
- No root glossary or ADR directory was present. Root agent/tracker/domain
  instructions were read before ticket/domain exploration. Public GitHub API
  reads supplied #47/#48 because `gh` has no authentication in this session.
- The research skill requests a background researcher; this session is itself
  the delegated research child and exposes no further agent-spawning tool.
  Research was performed here, with independent source reads parallelized.

## Confirmed local hardware and session facts

| Area | Read-only observation | Consequence / limit |
| --- | --- | --- |
| OS/kernel | Arch Linux, `BUILD_ID=rolling`; running `6.18.48-1-lts` | An LTS kernel is already running; it does not freeze userspace. |
| GPU | Lenovo ThinkPad T480 subsystem; Intel UHD Graphics 620 (`8086:5917`), driver `i915`; `i915` loaded; one visible DRM card (`card1`) and render node | No NVIDIA GPU appeared in the PCI inventory. No reason was found to plan proprietary-NVIDIA workarounds; actual Sway DRM/rendering remains untested. `lspci` warned it could not load libkmod resources, but printed driver-in-use data. |
| Graphics/input packages | Mesa/Vulkan Intel `26.2.5-1`, libinput `1.32.0-1`, Xwayland `24.1.14-1` | Existing open-driver Wayland stack, not proof of Sway compatibility. |
| Session | `XDG_SESSION_TYPE=wayland`, desktop Hyprland; Hyprland `0.56.2`; local seat0 session on tty2, `gdm-password`; GDM and `start-hyprland` observed | Current login route is GDM, not an assumed shell auto-start or active UWSM session. Display-manager startup is officially supported in Sway 1.12 [S6]. |
| Active left output | `DP-4`, HP E243i, 1920×1200 at 59.950 Hz, position 0,0, scale 1 | Matches current dual-home profile's intended placement. |
| Active right output | `DP-3`, Philips PHL 275E2F, 2560×1440 at 59.951 Hz, position 1920,0, scale 1 | Matches current dual-home profile; 74.97 Hz also advertised by Hyprland, but not active. |
| Internal output | eDP-1 connected in sysfs; 1920×1080 modes; current dual-home config disables it; absent from active Hyprland monitor list | Connected is not enabled. Laptop-only profile is configuration evidence, not a tested undocked session. |
| Dock/input | Thunderbolt bridges and ThinkPad Thunderbolt 3 Dock USB Audio input; Synaptics touchpad, IBM TrackPoint, external keyboard/mouse, MVMORIN STOMP keyboard interfaces, lid switch | Test dock reconnection, TrackPoint scrolling and all actual keyboards; do not infer their exact physical topology solely from PCI. |
| Keyboard | Hyprland reports `gb,se`, `grp:alt_shift_toggle`, active UK layout; configured repeat delay 250 ms/rate 40 | Sway exposes corresponding XKB/repeat controls [S4]; key bindings must work under both layouts. |

**Output discrepancy worth retaining:** the separate sysfs read listed only low
resolutions for `card1-DP-4` (640×480, 1024×768, 800×600, 848×480), whereas the
earlier live Hyprland query reported HP 1920×1200 active and advertised. This is
not diagnosed here and is not evidence that Sway will fail. Re-enumerate modes
and identifiers during a real trial, especially after dock/hotplug transitions.
Monitor serial numbers were read to establish identity but are omitted here.

Sway, swayidle, swaylock and xdg-desktop-portal-wlr were **not installed**.
Installed relevant tools include Waybar 0.15.0, wofi 1.5.3, wlogout 1.2.2,
swaync 0.12.6, grim 1.5.0, slurp 1.5.0, hyprshot 1.3.0, wl-clipboard 2.3.0,
cliphist 0.7.0, pamixer 1.6, brightnessctl 0.5.1, PipeWire/pipewire-pulse 1.6.10,
WirePlumber 0.5.18, and polkit-gnome. Swappy configuration exists in the repo,
but its package query reported absent: do not assume screenshot annotation is
currently a required or working workflow.

## Repository behavior and per-helper assessment

Local source links refer to the inspected baseline, not an invented work-i3
reference. Active `~/.config/hypr/hyprland.conf` and Waybar `config.jsonc` resolve
into this repository; `monitors_current.conf` resolves to `dual-home.conf`.

| Existing component / local evidence | Assessment for standard Sway (not implemented) |
| --- | --- |
| [Hyprland entry/config](../../hyprland/hypr/hyprland.conf), [general](../../hyprland/hypr/config/general.conf), [bindings](../../hyprland/hypr/config/keybindings.conf) | Rewrite configuration syntax and dispatches. Sway provides directional focus/move, workspaces, floating, fullscreen, split/tabbed/stacked layouts, modes, scratchpad and `exec` [S2]. Current dwindle/pseudo behavior is not an exact Sway layout contract; work-i3 habits take priority. Shell pipelines can remain shell pipelines. |
| [Window rules](../../hyprland/hypr/config/windowrules.conf) | Translate floating rules for pavucontrol/blueman/network editor and assignments (kitty→1, Chrome→2, KeePass2→9). Sway `app_id` applies to native Wayland; `class`/`instance` apply to Xwayland [S2]. Re-identify actual clients with `swaymsg -t get_tree`, rather than blindly copying Hyprland class regexes. |
| [Monitor profiles/cycler](../../hyprland/hypr/config/monitors/monitors.sh) | Generic idea (select a profile) is reusable; paths, Hyprland syntax and `hyprctl reload` are not. Sway has include/reload and direct output commands [S2,S3]. Decide later whether a tiny translated selector or existing output-profile tool is sufficient; no new monitor daemon is inherently required. |
| [Waybar config/modules](../../hyprland/waybar/config.jsonc) | Retain candidate, but replace `hyprland/workspaces` and `hyprland/language` with documented Sway modules and review options/CSS states; not just a global string replacement [S7,S8]. Tray, battery, clock and audio are not Hyprland dispatch integrations. |
| [Waybar reload helper](../../hyprland/waybar/reload.sh) | No Hyprland API use. Retain candidate, but it kills every Waybar process and reads global `~/.config/waybar`: shared paths could break a side-by-side fallback. Do not execute it during research. |
| [Audio/mic/brightness scripts](../../hyprland/hyprland-media-scripts/) | Generic pamixer/brightnessctl calls, not compositor APIs. Retain candidates with their runtime dependencies and permissions. Mic script contains `pamixer -u --default-source u`; the trailing `u` merits a separate functional check, not an assumption that migration fixes it. Brightness bindings are commented out; brightnessctl does not establish external-monitor brightness support. |
| [wofi](../../hyprland/wofi/config), [clipboard binding](../../hyprland/hypr/config/keybindings.conf) | Retain candidates. Existing `cliphist list | wofi -dmenu | cliphist decode | wl-copy` and one per-session `wl-paste --watch cliphist store` match upstream cliphist usage, including explicit Sway examples [S9,S10]. Verify text/images and Xwayland interoperation; do not start duplicate watchers on reload. |
| hyprshot screenshot bindings | Replace Hyprland-dependent selection/integration. grim + slurp cover region/output capture and clipboard pipes; upstream grim also gives a Sway IPC focused-window geometry example [S11]. A geometry crop is not the same as an isolated, unoccluded window image; pick the least-glue behavior that meets the later acceptance criteria. |
| [wlogout layout](../../hyprland/wlogout/layout) | UI is a retention candidate; logout is hard-coded `hyprctl dispatch exit 0`, lock is `hyprlock`. Session-specific actions must be separated. `swaymsg exit` is documented [S2]. Existing `systemctl suspend/poweroff/reboot` calls are not compositor APIs, but lock-before-suspend and authorization still need testing. |
| [hypridle](../../hyprland/hypr/hypridle.conf), [hyprlock](../../hyprland/hypr/hyprlock.conf) | Current explicit policy: lock after 300 seconds via logind, plus manual lock. No explicit before-sleep handler, output power timeout or auto-suspend in this repo config. Standard swayidle+swaylock are documented alternatives [S12,S13]; do not infer the current runtime is insecure from config alone or promise a lock theme translation. Retaining any cross-compositor Hypr tool would require separate protocol verification. |
| [hyprpaper](../../hyprland/hypr/hyprpaper.conf) and backgrounds | Static image can remain; Sway's `output ... bg ... fill` uses swaybg by default [S2,S3]. No need to port the Hyprland wallpaper configuration. |
| Autostart: polkit agent, swaync, blueman-applet, nm-applet | Generic desktop-service retention candidates, already observed running. Sway does not replace these services. Ensure each starts once, tray/notifications work, and graphical authorization prompts remain available; actual Sway tests are pending. |
| [Kitty](../../kitty/kitty.conf), [Alacritty](../../alacritty/alacritty.toml) | Kitty explicitly selects Wayland. Configured shell/editor/tmux behavior is not a Hyprland API dependency. Preserve integrations; actual focus/clipboard behavior remains untested. |
| [Arch installer](../../hyprland/install-hyprland-arch.sh), [general setup](../../setup-dotfiles.sh) | Preserve shell/symlink management approach, but do not run installers for a trial blindly. Desktop installer writes global shared config links and selects Hyprland packages. Existing comments about swaylock-effects/input inhibition and insufficient swap for hibernation are historical comments, not current standard-Sway incompatibility findings. |

## Documented compatibility and constraints

### i3 configuration, shell and IPC

Sway calls itself i3-compatible and supports much of the same configuration
model [S1]. Compatibility is not a guarantee that an entire i3 environment
ports: upstream's migration guide replaces xrandr/feh/input tooling, i3lock,
i3-msg and X11 clipboard/screenshot helpers, and notes quoting differences
[S5]. X11 automation that targets arbitrary windows does not automatically
control native Wayland clients. Work scripts must be supplied before auditing
these assumptions.

`exec` uses `sh`; `exec_always` repeats on reload [S2]. Persistent daemons should
not casually be moved into reload-triggered launches. IPC uses a Unix socket,
`SWAYSOCK` (also `I3SOCK`), i3 message framing, JSON replies and event
subscriptions. Commands, tree/workspace/output queries and Sway input/seat
queries are documented [S14]. Prefer supported fields and existing tools over
custom polling; undocumented reply fields are not a stable contract. The
protocol compatibility does not make `hyprctl` scripts compatible.

### Outputs, inputs and application matching

Sway supports resolution/refresh, global positions, scale, transforms,
enable/disable, and output power. It can match make/model/serial when connector
names change [S3]. Use Sway's actual enumerated modes/identifiers in a trial;
Hyprland connector names and rounded `@60` profiles are not proof of identical
Sway enumeration. Disabling an output removes its workspaces/windows from that
output; powering it off retains the workspace arrangement [S3]. This distinction
matters for dock profiles versus idle blanking.

Both observed external outputs use scale 1; no current fractional-scale
requirement was established. Sway documents fractional scaling but recommends
integer scaling and warns of Xwayland blur under HiDPI [S3]. Keep this as a
conditional future constraint, not a current blocker.

Sway exposes per-device/type settings for XKB layouts/options, repeat, touchpad
scroll/tap, pointer acceleration and TrackPoint-style button scrolling. Keyboard
grouping can synchronize matching keyboard devices [S4]. Actual identifiers
come from Sway, not Hyprland. Lid bindings are supported [S2], but policy must
be reconciled with logind/docked behavior; no lid/suspend experiment was run.

### Lock, idle and suspend

The documented swayidle recipe combines `-w`, timeout locking and a
`before-sleep 'swaylock -f ...'` handler. `-w` waits for the lock command and
`swaylock -f` detaches after locking; logind's inhibitor delay remains bounded
by `InhibitDelayMaxSec` [S12,S13]. swayidle also handles logind lock events.
These are mechanisms, not an audited policy for this laptop.

Trial criteria need manual/logind/idle locks, suspend from the menu and lid,
resume, dock/undock while locked, both keyboard layouts, and authentication.
Keep screen power-off and actual suspend distinct. Hibernation is not promised:
the installer's old swap comment is not a current swap/resume assessment.

### Portals and screen sharing: check versions, not old folklore

Observed installed portal stack: xdg-desktop-portal 1.22.1, Hyprland backend
1.4.1, GTK backend 1.15.3. System `hyprland-portals.conf` selects
`hyprland;gtk`; no user portal config directory was present. A Sway session
must not accidentally inherit that backend selection or stale Hyprland
environment. Portal configuration is selected using `XDG_CURRENT_DESKTOP`,
with desktop-specific files and user overrides [S15]. xdpw documents importing
`WAYLAND_DISPLAY` and the correct desktop into D-Bus [S16]. Retain Hyprland's
own selection for fallback rather than globally forcing one backend.

The wlroots backend implements Screenshot and ScreenCast, not every portal;
GTK can supply missing implementations such as file dialogs [S16]. Existing
PipeWire/WirePlumber availability is necessary context, not a successful browser
sharing test. The xdpw interface list does not imply RemoteDesktop support.

**Important current-version correction:** upstream's latest releases at research
time are Sway **1.12** and xdpw **0.8.4**. Sway 1.12 explicitly adds individual
window capture [S6]. Released xdpw 0.8.4 supports window targets and advertises
them when the required capture protocols exist; its chooser manual accepts
`Window: <identifier>` as well as `Monitor: <name>` [S17,S18]. Therefore
“Sway/wlr can only share full monitors” is not a valid blanket 2026 constraint.
This is documented capability, **not tested end-to-end on this machine**.
The selected package versions, chooser, browser/client and portal selection
must all cooperate. A monitor-only chooser does not expose every supported
target. Confirm the intended browser/conferencing app, monitor versus isolated
window selection, cancellation, and repeated sharing after session switches.
Do not invent a mandatory conferencing/remote-control workflow.

### Transparency and appearance

Standard Sway documents per-window `opacity` from 0 to 1 [S2]; it is not
necessary to choose an effects fork for optional transparency. This changes
the window as a whole, including text/content. Kitty's `background_opacity`
instead changes its terminal background cells and has documented color/theme
caveats and performance cost [S19]. These are distinct controls and may
combine; neither means every application's background can be made selectively
transparent by the compositor.

Current Hyprland config requests active/inactive whole-window opacity
0.95/0.80 plus blur, shadows, rounding, gradients and animation. Standard Sway
1.12's documented command interface/registry has opacity but no corresponding
blur/shadow/rounding/animation configuration [S2,S20]. Do not promise visual
parity or add focus-event glue to reproduce optional opacity behavior. The map
already makes transparency optional, so this is a tradeoff, not a blocker.

## Maintenance risk and safe trial boundaries

**Inference:** an i3-like configuration with fewer effects and fewer
Hyprland-specific helper calls is a plausible way to reduce local compositor
configuration churn. Neither upstream docs nor this single-machine inventory
quantifies future churn or proves Sway will require less maintenance.

Arch remains rolling release: kernel/i915, Mesa, wlroots, Wayland protocols,
portals, PipeWire, applications and generic helpers can still regress. Sway 1.12
itself depends on wlroots 0.20.0 [S6]. Arch explicitly does not support partial
upgrades, recommends full upgrades, reading news, dealing with changed config
files and rebuilding locally built packages after relevant ABI changes [S21].
Freezing just the compositor is not an update-proof strategy. The observed LTS
kernel reduces neither userspace update obligations nor the need for backups.

Research constraints for the later migration plan:

1. Preserve a separately selectable Hyprland session; actual Sway login and
   fallback through GDM remain untested. No session files were modified.
2. Separate compositor config, portal selection, autostarts and shared Waybar/
   wlogout paths enough that a Sway trial cannot silently overwrite fallback.
   Reuse compatible tools rather than introducing a new desktop framework.
3. Validate output modes/names, dock/hotplug/laptop-only, keyboard layouts,
   focus/move/layout/workspaces, rule matching, clipboard/screenshots, tray,
   notifications, audio/mic, authorization, lock/idle/suspend/resume and any
   agreed sharing workflow during the required side-by-side daily-use trial.
4. Let the human workflow/stack/trial decisions select exact bindings, components
   and acceptance criteria. This document supplies evidence, not implementation
   or an approved migration specification.

## Questions surfaced, not additional scope

- Work-i3 configuration/scripts are still missing. Which exact habits and
  X11-specific helpers must be retained? Existing workflow decision should cover it.
- Is whole-monitor sharing sufficient, or is isolated window sharing required,
  and in which actual client? Existing workflow/acceptance decisions should cover it.
- How should dock/undock, laptop lid and suspend interact, and which failures
  reject the trial? Existing stack/trial decisions should cover it, including the
  observed DP-4 mode discrepancy.
- No target choice or human decision ticket is resolved by this research.

## Primary sources

Sources accessed 2026-10-25. Released Sway 1.12/xdpw 0.8.4 sources are pinned
where behavior is version-sensitive; moving docs describe capability, not an
installed version. Local observations above are explicitly sourced by command
and repository path rather than represented as external facts.

- **S1:** [Sway project README](https://github.com/swaywm/sway/blob/1.12/README.md).
- **S2:** [Sway 1.12 configuration/commands/criteria](https://github.com/swaywm/sway/blob/1.12/sway/sway.5.scd).
- **S3:** [Sway 1.12 output manual](https://github.com/swaywm/sway/blob/1.12/sway/sway-output.5.scd).
- **S4:** [Sway 1.12 input manual](https://github.com/swaywm/sway/blob/1.12/sway/sway-input.5.scd).
- **S5:** [Sway upstream i3 migration guide](https://github.com/swaywm/sway/wiki/i3-Migration-Guide) (moving wiki).
- **S6:** [Sway 1.12 release notes](https://github.com/swaywm/sway/releases/tag/1.12).
- **S7:** [Waybar Sway workspaces manual](https://github.com/Alexays/Waybar/blob/master/man/waybar-sway-workspaces.5.scd).
- **S8:** [Waybar Sway language manual](https://github.com/Alexays/Waybar/blob/master/man/waybar-sway-language.5.scd).
- **S9:** [wl-clipboard upstream README](https://github.com/bugaevc/wl-clipboard/blob/master/README.md).
- **S10:** [cliphist 0.7.0 README and Sway/wofi examples](https://github.com/sentriz/cliphist/blob/v0.7.0/readme.md).
- **S11:** [grim author's upstream README and capture examples](https://github.com/emersion/grim/blob/master/README.md) (author-maintained mirror notes move to [SourceHut](https://sr.ht/~emersion/grim/)).
- **S12:** [swayidle manual](https://github.com/swaywm/swayidle/blob/master/swayidle.1.scd).
- **S13:** [swaylock manual](https://github.com/swaywm/swaylock/blob/master/swaylock.1.scd).
- **S14:** [Sway IPC manual](https://github.com/swaywm/sway/blob/1.12/sway/sway-ipc.7.scd).
- **S15:** [XDG Desktop Portal backend configuration](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html).
- **S16:** [xdg-desktop-portal-wlr upstream README](https://github.com/emersion/xdg-desktop-portal-wlr/blob/v0.8.4/README.md).
- **S17:** [xdpw 0.8.4 capture protocol/source negotiation](https://github.com/emersion/xdg-desktop-portal-wlr/blob/v0.8.4/src/screencast/wlr_screencast.c), [target handling](https://github.com/emersion/xdg-desktop-portal-wlr/blob/v0.8.4/src/screencast/screencast.c).
- **S18:** [xdpw 0.8.4 chooser manual](https://github.com/emersion/xdg-desktop-portal-wlr/blob/v0.8.4/xdg-desktop-portal-wlr.5.scd), [release](https://github.com/emersion/xdg-desktop-portal-wlr/releases/tag/v0.8.4).
- **S19:** [Kitty background opacity](https://sw.kovidgoyal.net/kitty/conf/#opt-kitty.background_opacity).
- **S20:** [Sway 1.12 command registry](https://github.com/swaywm/sway/blob/1.12/sway/commands.c).
- **S21:** [Arch project's system maintenance guidance](https://wiki.archlinux.org/title/System_maintenance#Partial_upgrades_are_unsupported).
