# W102D 2 GB / 16 GB capacity trial

The current v3 recipe requires the Bluetooth-startup and wireless-fixed W103D KDE v7 assembly.
See [the shared v7 recipe](../../w103d/burn/v7-README.md) for preparation and module identities.
The previous v2 derived from the pairing-fixed W103D KDE v6 assembly. The original
v1 used W103D v5 at `2bf9c0b34c1a6086a8b86a6ba90c81fc184a6947`. The owner reports that W102D and
W103D use the same factory flashing package. This trial changes only eMMC
capacity handling; **W102D hardware boot has not yet been verified**.

The W103D bootstrap accepts exactly 60,620,800 sectors, so it rejects a
16 GB device before configuring the Linux boot path. The W102D bootstrap
reads the runtime eMMC size from sysfs, accepts 28,000,000–33,554,432 sectors,
and cross-checks the EPT data partition size against that capacity. The root
partition begins at sector 4,001,792 and ends at the actual device end.
The reference DTB already defines the data partition as remaining capacity.
EPT offsets, filesystem signatures, environment CRC and write readback
checks are retained. Malformed or out-of-range capacities are rejected.

DDR/U-Boot, vendor kernel, vendor DTB, Linux 6.18.49-ophub, MT7663S driver and
firmware, root filesystem, boot filesystem, logo and desktop settings remain
identical to the supplied W103D base (v6 for this release). Internal W103D board identity, environment boot command
names and filesystem labels intentionally remain unchanged for this trial.
The 8 GiB initial root filesystem fits the 16 GB layout and expands on first
startup. See [the W103D recipe](../../w103d/burn/README.md) for shared boot
design, prerequisites and binary provenance.

## Build and verify

Use Linux, Python 3.11+, clang/lld, qemu-arm-static, device-tree-compiler and
the existing Khadas packer. First prepare and verify a clean W103D v6 assembly
using [the pairing fix recipe](../../w103d/fixes/bluedevil/README.md). Keep its raw
files, payloads and `checks/final-package.json`. Supply the same logo BMP.
The W102D output directory must not exist and must be on the same filesystem
as the base: unchanged inputs are hardlinked and must remain immutable.

```sh
bash board/w102d/burn/build.sh \
  /work/w103d-v7 /work/w102d-v3 /work/khadas-tools /work/bootup.bmp
```

The build runs 26 ARM provisioning tests, produces the new bootstrap, packs
and verifies the container, and checks that only boot/recovery and their
VERIFY items differ from the base. Shared packaging utilities are reused
directly from `board/w103d/burn`. No kernel module is rebuilt.

v2 inherits BlueDevil `4:6.3.4-2+w103d1`, which removes the wizard's unconditional
disconnect after pairing (KDE `dff9c79c`). This addresses the GUI keyboard pairing
failure verified on W103D. It also inherits the pin preventing replacement by an
unvalidated BlueDevil version. The 16 GB provisioning logic is unchanged from v1.
This shared userspace repair has not yet been tested on W102D hardware.

To run the provisioning tests independently:

```sh
python3 board/w102d/burn/test_bootstrap.py --output /work/w102d-tests
```

Seven accepted capacities cover successful provisioning and repeat execution.
Nineteen rejection cases cover corrupt metadata, filesystems and capacity
arguments, with no writes to the inspected storage regions. These fixtures
exercise ARM code under QEMU; they do not emulate the hardware sysfs discovery
path, USB flashing or real board boot.

## Existing v1 artifact validation

The locally generated `W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v1.burn.img`
is 4,646,524,272 bytes with SHA-256:

```text
3af4477f9e5a15398ca24c0543dfebcb4737ec5d55861afc6d625e0c7765e460
```

All 26 provisioning tests and the packer/container checks passed. The boot
and root raw images and embedded vendor kernel match W103D v5 byte for byte.
Only boot/recovery bootstrap payloads and their VERIFY records changed.
The binary image is a local test artifact and is not stored in Git.

First startup provisions the boot path and reboots once; allow 3–5 minutes.
The inherited desktop logs in automatically as `armbian / 1234`; root also
uses `1234`. Change these passwords after installation. No saved Wi-Fi
credentials are included. A successful W103D test does not establish W102D
compatibility; this package still needs the owner's W102D flash test.

## v3 startup and wireless requirements

v3 inherits BlueZ AutoEnable and KDE launchState=enable, so KDE does not
restore a saved adapter-off state at login. The default user and future
users get the same policy. Pair a mouse once after a clean flash; no device
bonds or rfkill snapshots are shipped.

Both the MT7663S connection-probe repair and mac80211 payload-rate reporting
repair are mandatory. The builder verifies the v7 reports and independently
mounts the base root/boot read-only to check the actual module hashes, ABI,
Bluetooth settings and absence of embedded wireless modules in initramfs.
An old v6 root or old same-release module cannot pass by changing its filename.
The root/boot payloads still remain identical to the supplied W103D base.
Scanning packet loss remains unresolved, and W102D hardware boot and Bluetooth
reconnection still require device validation.
