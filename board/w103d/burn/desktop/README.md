# W103D KDE desktop image

Target: Debian Trixie arm64, Linux `6.18.49-ophub`, the project's 32 GB W103D.
Use a clean server root image. Never clone a configured user's root filesystem.

Defaults are explicitly requested by the image owner: hostname `armbian`,
root password `1234`, ordinary desktop user `armbian` with password `1234`,
SDDM auto-login into Plasma Wayland, no first-login account wizard.

The package list includes offline NetworkManager/nmtui, Chinese locale/fonts,
Fcitx 5 Chinese addons, KDE desktop and PipeWire. `configure.sh` installs the
tested HDMI UCM and S16LE/48 kHz stereo policy, memory settings, first-run
desktop layout and SSH host-key recovery. Execute it inside the ARM64 root
with `W103D_DESKTOP_SOURCE` pointing to this directory and a copy of the parent
`ssh-hostkeys.conf`. Its `systemctl` calls are intended for an offline root;
on a live machine they change enable/mask state and require a controlled
network transition. Do not run it blindly over an existing networkd SSH session.

Before configure.sh, install packages.list with Debian's package manager,
apply `../sanitize_overlay_modes.py ROOT --apply` to imported Windows overlays,
and run `../retire-base-kernel-record.sh` only if its strict preconditions match.
Use policy-rc.d while preparing an offline root. The build host needs binfmt/QEMU
for ARM64 chroot commands and librsvg2-bin to render the original W103D.svg.

Install these pinned third-party resources under /usr/share:

| Resource | Source/version | Destination |
| --- | --- | --- |
| Moe Plasma style | KDE Store 1284575, 3.2; archive SHA256 `61447f8787cfab00684ac97a41198b6cd779a76b405efc0641136a44f663406b` | plasma/desktoptheme/Moe |
| Moe colors | KDE Store 1284573, 1.7; SHA256 `ae907ace0f67884622571f3ddaa8cfa08a5cff9c7441cff204b313dd65d0f3cc` | color-schemes/Moe.colors |
| Colloid | vinceliuice/Colloid-icon-theme commit `ceac6608ecd0e40025cbc2ebbd32bf0e0f4ebc6a` | icons/Colloid, Colloid-Light, Colloid-Dark |
| Panel Colorizer | luisbocanegra/plasma-panel-colorizer commit `f144a27d4c339cf146fdad5ecacb26d36877e939` | plasma/plasmoids/luisbocanegra.panel.colorizer |

Install Colloid into an empty staging directory with its `install.sh -d DEST -p`.
Copy the Panel Colorizer `package/.` contents into its target; its optional C++
blur plugin is not required. Preserve licenses and authors. Render the original
wallpaper with `rsvg-convert -o /usr/share/wallpapers/W103D.png W103D.svg`.
The default layout uses the two pinned Colorizer presets with blur disabled.
No online weather/location widget or animated splash is required.

After configuring the root, restore the target's resolver link and apt sources,
remove policy-rc.d and build temp files, SSH host keys, random seeds and logs;
leave machine-id empty with /var/lib/dbus/machine-id linked to /etc/machine-id.
Do not include any Wi-Fi connection profile, SSH authorization/private key,
test files, user's home or board-generated MAC override. Do not create the swap
file in the shipping image. Run `verify-root.py ROOT` before packaging.

Assemble with the already validated server/bootstrap work directory:

```sh
bash board/w103d/burn/assemble-desktop.sh \
    /work/server-assembly /work/desktop-rootfs.raw /work/kde-assembly /work/tools
python3 board/w103d/burn/verify_package.py /work/kde-assembly --logo /work/bootup.bmp
```

The assembler requires zerofree and checks the complete kernel/module/initramfs
set, desktop defaults, default password hashes, absent per-image identities,
FAT/ext4 integrity and the vendor container. Independent package verification
checks all payloads, SHA-1 VERIFY items and expanded sparse hashes.

Hardware validation on 2026-09-06: eMMC boot/reboot; Chinese KDE with Panfrost;
automatic ordinary-user session; actual Chinese input/candidate display; user
confirmed HDMI sound after S16LE routing and no garble after `osd close`;
NetworkManager wired DHCP and Wi-Fi scan; SSH root login; zram and swap after
reboot. These checks precede the v2 container's subsequent user flash test.

## KDE v3: black-screen reproduction and always-awake policy

On the user's subsequent board session, opening Overview with desktop OpenGL
3.1 produced a black screenshot and 6,032 new GL errors in one test. Disabling
idle power management alone did not prevent this. This matches the OpenGL 3.1
failure described in [KDE bug 486460](https://bugs.kde.org/show_bug.cgi?id=486460).
With `kwin-gles.conf`, KWin uses `KWIN_COMPOSE=O2ES`: the reported GPU remains
Mali-G31/Panfrost and the actual context is OpenGL ES 3.1. The same Overview
test and 20 consecutive open/close cycles produced no new GL errors. Install
the drop-in under `etc/systemd/user/plasma-kwin_wayland.service.d/`; it applies
only to the default Wayland compositor, not to every application.

The owner also requested no automatic power saving or sleep. `configure-power.py`
sets Plasma 6's `DimDisplayWhenIdle=false`, `TurnOffDisplayWhenIdle=false`,
`AutoSuspendAction=0` for AC, Battery and LowBattery, and disables automatic
locking. It configures `/etc/xdg`, `/etc/skel` and the factory desktop account.
systemd sleep configuration and unit masks block suspend, hibernate, hybrid
sleep and suspend-then-hibernate; logind ignores idle, lid and sleep-key actions.
X11 greeter/session timers and NetworkManager's Wi-Fi power-save default are
disabled too. The boot command explicitly includes `consoleblank=0`.
Normal shutdown/reboot and thermal protection remain available. The v3 idle
policy itself did not change CPU frequency selection; v4's CPU policy is below.

The policy was applied live and checked after reboot. `CanSuspend` and
`CanHibernate` returned `no`; Wi-Fi reported power save off. A controlled
desktop restart then verified the persistent GLES drop-in. Both changes are
reproduced in the clean shipping root, without copying board network profiles.

New Wi-Fi connections also use Plasma NM's `General/SystemConnectionsByDefault=true`
in `plasma-nm` (system defaults, skeleton and factory account). This avoids
depending on an encrypted user wallet during automatic login. Plasma NM 6.3.6's
`UiUtils::setConnectionDefaultPermissions` uses system-owned secrets when this
option is set and the active desktop can modify system connections. That
authorization was checked on the board. KWallet remains available for other
applications. NetworkManager stores entered Wi-Fi secrets in root-only 0600
keyfiles on the user's device; the image itself has no network profile or PSK.

`disable-legacy-startup.py` removes only the exact generic custom_service call
from rc.local. The imported script failed to parse because of CRLF line endings;
enabling it would additionally introduce delayed SSH restarts and generic device
management outside this board's validated systemd service setup. Other rc.local
customizations are preserved. The cleaned rc-local unit was rerun successfully
on the board.

## KDE v4: associated scans and CPU response

The MT7663S driver now sends the native N9 BSS RLM channel context before
online scans and uses firmware-default scan timing. Twenty full-channel scans
across 2.4/5 GHz and after reboot preserved the same association. Concurrent
512 MiB transfers in each direction completed while scanning. Off-channel
scanning still causes loss/latency and lower throughput; KDE's scan requests
were not suppressed. See `../../linux/6.18-validation.md` for measurements.

`performance.sh` selects the existing performance governor only when policy0
reports the tested maximum of 1,800,000 kHz. No OPP, voltage or thermal limit
is changed. A three-minute four-core board stress test peaked at 70.7 C;
reboot verified persistence. To revert on a running board, disable
`w103d-performance.service`, select schedutil in `/etc/default/cpufrequtils`,
and write `schedutil` to policy0's `scaling_governor`.

To update an unconfigured v3 image, copy its raw root filesystem to a new
workspace, mount the copy, then run:

```sh
bash board/w103d/burn/update-desktop-root.sh /work/mounted-root /work/mt7663s.ko /work/mac80211.ko
python3 board/w103d/burn/desktop/verify-root.py /work/mounted-root
```

The current updater requires both separately built, tested `6.18.49-ophub` modules, built with
`ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LOCALVERSION=-ophub`.
The historical v4 tested module SHA-256 was
`1f0f1456c311423dd7f2eb189c805a689515d3cb3a93f810cd74cd995df78737`.
Current v7 uses the newer pair pinned in `../wireless-modules.json`; the old
v4 artifact is rejected. The updater checks exact hashes, ABI, dependencies
and SDIO alias, installs both modules, runs depmod and configures Bluetooth
startup and CPU policy. Unmount before calling the assembler. The assembler
rejects embedded initramfs MT7663S/mac80211 copies. Never mix a retained 6.12
module. See the [v7 recipe](../v7-README.md) for clean v6 migration.

The clean image contains no Wi-Fi profile, password, AP/BSSID or band lock.
The test board's 5 GHz-only connection remains a local user configuration.

## KDE v5: preserve board components during APT upgrades

An actual 26.8.1 to 26.8.3 upgrade in a v4 image copy removed the W103D DTB:
the generic `linux-dtb-current-meson64` preinst deletes `/boot/dtb` and the
official replacement package does not contain this board. The original
Odroid N2 BSP also replaced `/etc/armbian-release` and the generic boot scripts.

`protect-upgrades.py ROOT` installs `upgrade-protection.pref` and holds the
installed BSP, firmware, Image, DTB, U-Boot and header packages. The negative
APT priority also excludes new generic kernel/board packages and continues
to work if an installed package's hold is removed. The script validates the
prepared W103D root and package registrations before changing anything, and
is idempotent. Both the fresh desktop configuration and incremental clean-root
update invoke it; `verify-root.py` checks the resulting holds and preferences.

Debian applications, libraries and security updates remain available. The
matched `6.18.49-ophub` kernel, board identity and tested firmware remain fixed;
a base-files update can have a newer version without replacing this board BSP.
This is intentional isolation of the board components, not support for
installing arbitrary official Odroid N2 kernels. A future matched W103D kernel
upgrade must deliberately adjust this policy and verify the complete ABI set.

The policy applies to normal APT resolution; direct `dpkg -i`, explicit version
overrides or manually deleting files are outside it. It does not repair an
already missing DTB or change the vendor bootloader's fallback behavior.
