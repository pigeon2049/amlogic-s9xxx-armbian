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
bash board/w103d/burn/assemble-desktop.sh \
  /work/w103d-v6 /work/kde-v8/rootfs.raw /work/w103d-v8 /work/khadas-tools
python3 board/w103d/burn/verify_package.py /work/w103d-v8 --logo /work/bootup.bmp
```

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
