# W103D experimental USB Burning Tool image

Current desktop recipe: [KDE v7 Bluetooth startup and wireless fixes](v7-README.md).
It requires both tested wireless modules and rejects older same-release copies.

This is a board-specific image recipe for the
32 GB W103D with 60,620,800 eMMC sectors. Its normal runtime is
`6.18.49-ophub`. It uses the tested 2021 N9 firmware, SHA-256
`223f73f17f0f986dc4e7167daa6eef14ffb41c713f22d70f9645eb049bdec80a`.

The user flashed v1 and eMMC boot was verified. KDE v2 settings were then
installed and tested on that board before being reproduced in a clean image.
The user's subsequent desktop session exposed a reproducible OpenGL 3.1
black-screen bug when opening Overview. KDE v3 uses KWin's hardware GLES path
and disables automatic display dimming, blanking, locking and system sleep.
KDE v4 adds the board-tested associated-scan driver repair and the existing
1.8 GHz CPU performance policy. KDE v5 adds APT protection for the matched
board components after reproducing the generic DTB package deleting the
W103D DTB during an upgrade. Debian userspace updates remain available.
KDE v6 backports the upstream BlueDevil pairing fix and pins the tested package;
see [the fix and clean-image build instructions](../fixes/bluedevil/README.md).
New containers require a separate flash test;
live driver/configuration validation is not a claim of flashing that container.
See `desktop/README.md` for tested settings and build inputs.

## Boot design

Keep the DDR/U-Boot, platform configuration and complete EPT/DTB partition
layout from the locally verified slimBOXtv reference image. That image is a
third-party Android distribution, not a verified unmodified OEM release.

The original 16 MiB Android `boot` partition cannot hold the 6.18 Image and
initramfs. `boot` and `recovery` therefore contain the unchanged reference
ARM32 Linux 4.9.113 kernel with a small, new initramfs. Its freestanding ARM
`/init` checks the actual eMMC size, EPT offsets, filesystem signatures and
U-Boot environment CRC before installing an MBR view and boot commands.
It writes only bytes 440–511 of the user area's first sector and the 64 KiB
environment at 180 MiB, preserves other environment keys, fsyncs and checks
readback, then reboots. It does not run Android userspace.

On subsequent normal boots, U-Boot loads the actual 6.18 Image, uInitrd and
Linux DTB from FAT using `emmc_autoscript` and `booti`. The vendor kernel
remains available in the bootstrap/recovery partitions as a fallback. This
design was used by the user-flashed v1. Subsequent eMMC root mounts and reboots
were verified. Do not generalize this one board's result to other eMMC layouts.

| EPT partition | Offset | Linux use |
| --- | ---: | --- |
| env | 180 MiB | Original 8 MiB reservation; patch first 64 KiB |
| logo | 196 MiB | Original 8 MiB reservation; supplied bootup BMP |
| boot | 316 MiB | First-start bootstrap, within original 16 MiB |
| system | 730 MiB | MBR p1, 1 GiB FAT32, `W103D_BOOT` |
| data | 1954 MiB | MBR p2, rest of this eMMC, `W103D_ROOT` |

The server root starts as 4 GiB ext4; KDE v2 starts as 8 GiB. A first-start service runs
`resize2fs` within the already full-size MBR partition. The generic ophub
partition resize path is disabled; no partition editor runs at startup.
This is an Armbian installation, not an Android/Armbian dual boot image.

## Local build

Prerequisites: a clean W103D Armbian base image built with the complete,
matched 6.18 components; the unpacked reference package; the chosen logo;
the pinned Khadas tools; root on Linux with loop devices, dosfstools,
e2fsprogs, U-Boot tools, clang/lld, Python 3.11+ and qemu-user-static.
The current logo input path is recorded in `assemble.sh`; change it for
another workspace. Use an empty assembly directory.

```sh
python3 board/w103d/burn/test_bootstrap.py --output /work/bootstrap-tests
bash board/w103d/burn/assemble.sh \
  /work/Armbian_w103d_6.18.49.img.gz /work/assembled \
  /work/reference-unpacked /work/khadas-tools
python3 board/w103d/burn/verify_package.py /work/assembled \
  --logo /work/bootup.bmp
```

The clean input is rebuilt from official Armbian, not cloned from the test
board. `assemble.sh` checks the component set, strips SSH host identities,
creates explicit-zero Android sparse images, builds the bootstrap, packs
the container, checks it with the vendor packer and writes its hash.
`verify_package.py` additionally compares each payload, every VERIFY SHA-1,
sparse expansion SHA-256/CRC, Android boot digest/initramfs and logo bytes.
The QEMU tests exercise provisioning, repeat execution and rejection of
bad EPT, environment and root filesystem signatures without writes.
They do not emulate board boot or USB flashing.

Kernel modules must have exactly the runtime's release in vermagic, with
`LOCALVERSION=-ophub`; do not mix the retained 6.12 rollback modules into
the 6.18 image. Existing W103D validation also checks the firmware hashes,
MT7663S dependency list and SDIO alias.

## Distribution boundary

The new bootstrap and assembly source has its own license notices. The
reference boot firmware, reference Linux kernel, MediaTek firmware and
packing binaries retain their respective licensing/provenance. In
particular, the exact 2021 N9 firmware's redistribution terms remain an
upstream review item. Do not label the complete binary image GPL or publish
it as a board-tested release based solely on these offline results.
