# KDE v8: correct Bluetooth startup and ordinary-user ping

Same-version boot repair: the first v8/v4 artifacts contained CRLF in the
compiled eMMC script because Windows git archive applied core.autocrlf.
`.cmd` now has explicit LF attributes. Assembly checks source and compiled
legacy script CRCs/content, and final package verification extracts the
script from the actual FAT image using mtools. Repaired files replace the
original v8/v4 names; do not increment release numbers without user approval.

W103D v8 and W102D v4 replace the ineffective `[General]` Bluetooth policy
in v7/v3 with `[Global]`, as read by the shipped BlueDevil 6.3.4. They also
install `net.ipv4.ping_group_range = 0 2147483647` through sysctl.d so normal
desktop users can ping without depending on file capabilities or setuid.
See [desktop-permissions-validation.md](desktop-permissions-validation.md).

The existing tested wireless module pair, pairing backport, APT protection,
Chinese KDE defaults and boot layout are retained. No kernel rebuild is
required. Exact complete `6.18.49-ophub` vermagic and pinned module hashes
are checked before installation and again during assembly.

```sh
bash board/w103d/burn/prepare-wireless-root.sh \
  /work/w103d-v6/rootfs.raw /work/kde-v8 \
  /work/connection-rate-final.ko /work/mac80211-data-rate.ko
mount -o loop /work/kde-v8/rootfs.raw /work/kde-v8/root
bash board/w103d/burn/install-desktop-packages.sh \
  /work/kde-v8/root /work/kde-v8/checks
umount /work/kde-v8/root
bash board/w103d/burn/assemble-desktop.sh \
  /work/w103d-v6 /work/kde-v8/rootfs.raw /work/w103d-v8 /work/khadas-tools
python3 board/w103d/burn/verify_package.py /work/w103d-v8 --logo /work/bootup.bmp
```

The same v8/v4 filenames now also include the complete desktop package list:
notification/XDG tools, Vulkan ICDs and diagnostics, file/archive/media tools,
GTK4/Qt5 input frontends, viewers/thumbnails, GTK theme integration, wallet,
SMB/exFAT tools, Discover/PackageKit, printing, KDE Connect, LibreOffice with
KDE integration, Simplified Chinese UI/offline help, Java/report support,
office-compatible fonts, and Chinese Firefox.
KDE translations ship with the individual Debian KDE packages. There is no
separate obsolete kde-l10n-zhcn package to install on Plasma 6.

The offline package installer requires ARM64 binfmt, uses private mounts and
policy-rc.d, restores the resolver and Armbian sources, and rejects package
removals or changes to board/boot/pairing packages. It does not run a full
distribution upgrade. Assembly checks every explicit package or its provider,
key executables, Chinese resources and both Vulkan ICD files. PanVK remains
experimental on Mali-G31 and is not enabled globally; KWin keeps its tested
Panfrost OpenGL ES backend. Package presence is not hardware Vulkan validation.

With the prepared root mounted, `desktop/test-applications.sh ROOT CHECKS_DIR`
uses actual ARM64 binaries as the ordinary user, exports a Chinese document
with headless LibreOffice, checks extracted PDF text and enumerates Lavapipe.
It needs ARM64 binfmt and host `pdftotext` (poppler-utils). Profiles and test
input use a private tmpfs; the shipping root is not personalized by the test.

The baseline migration check explicitly permits only the absence of the new
ping policy; all other desktop checks remain required. Final-root checks
always require the new policy and correct Bluetooth group.

To verify ordinary-user permissions on Linux, mount a prepared root, register
ARM64 binfmt/QEMU, then run as root:

```sh
bash board/w103d/burn/desktop/test-ping-root.sh /work/mounted-root
```

The test uses private network/mount namespaces and the actual image binaries.
It reproduces the old failure, checks IPv4/IPv6 Echo sockets without NET_RAW,
and verifies the image's systemd-sysctl restores permission after a reset.
It is not a board reboot or Bluetooth hardware test.

The W102D branch consumes the verified W103D v8 assembly:

```sh
bash board/w102d/burn/build.sh \
  /work/w103d-v8 /work/w102d-v4 /work/khadas-tools /work/bootup.bmp
```

New output directories must not exist. W102D input and output must be on the
same filesystem for immutable hardlinks. W102D retains its 16 GB capacity
bootstrap; other payloads match W103D. Clean images contain no Wi-Fi profiles
or Bluetooth pairing keys. Pair peripherals once after flashing. Hardware
mouse reconnection and W102D compatibility remain to be verified; existing
wireless scan packet loss is not addressed by this userspace change.
