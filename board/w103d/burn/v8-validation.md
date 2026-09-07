# W103D v8 / W102D v4 release validation

Date: 2026-09-07. Same-version replacement after the reported logo/reboot loop.
The original v8/v4 files were defective and their original hashes are superseded.
The repaired files retain the same names and overwrite the delivery paths.
Built with the unchanged desktop root and corrected boot scripts from:

- W103D `w103d-burn-6.18`: `83aed3a6a02393583e891be3e5c9154a9e3ff889`.
- W102D `w102d-burn-6.18`: `1a4786bb903be003821da3031b46028e99462560`.

The source snapshots are included in each delivery. Later documentation-only
commits record the results and do not change the inputs used for these images.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| W103D_Armbian_26.8.1_6.18.49_KDE_v8.burn.img | 4698948768 | `cd87d6bec89ba28e483b52444228b3df410dab3b97f97b1596be91ab6387626f` |
| W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v4.burn.img | 4698952864 | `915a54195dec53906e3c8dc61b3c4a1bd46d2a2b26dd90ae64c09d0b3a89ed86` |

Both include corrected BlueDevil 6.3.4 `[Global]` startup policy and persistent
ordinary-user ICMP Echo permissions. Actual ARM64 ping under QEMU, uid/gid
1000 and without NET_RAW, reproduces the old failure, then passes IPv4 3/3,
IPv6 3/3 and repeated systemd-sysctl startup application. Real kreadconfig6
returns Global/launchState=enable at all three config locations.
For read-only image QA, Qt uses offscreen mode and a temporary writable
XDG_CONFIG_HOME in a private mount namespace; the image remains unchanged.

Clean-root migration, full desktop checks, Bluetooth policy/identity checks,
pairing backport, exact tested wireless hashes, complete 6.18.49-ophub ABI,
firmware, DTB/Image/initramfs, filesystems, container integrity, every payload
and VERIFY record, sparse expansion, bootstrap init and logo checks pass.
No kernel or module was rebuilt. Initramfs contains neither wireless module.

W102D passes all 26 ARM capacity-bootstrap tests. Its raw rootfs and bootfs
are identical to W103D; only boot/recovery provisioning payloads and their
VERIFY records differ. Its 16 GB support remains a hardware trial.

The identical desktop root additionally passes a QEMU virt system boot,
SSH host-key generation and root/armbian SSH logins in disposable snapshots.
This direct kernel boot bypasses physical U-Boot; it is not a hardware flash. Mouse reconnection after real startup remains unverified. Existing
scan packet loss is not addressed. Original v7/v3 delivery files are retained.

Windows deliveries:

- `output/releases/W103D_6.18.49_KDE_USB_Burning_v8/`
- `w102d/output/W102D_6.18.49_KDE_16GB_USB_Burning_v4/`

Each contains the burn image, SHA-256 sidecar, manifest, instructions, checks
and source archive. Build recipe: [v8-README.md](v8-README.md).

## Boot-loop diagnosis and regression prevention

Windows Git archive with core.autocrlf=true converted the unqualified .cmd
source from 663 LF bytes to 678 CRLF bytes; mkimage packed it without complaint.
The original boot FAT contains that CRLF source and compiled payload. A host
replay of the Khadas v2015.01-family Hush parser (hardware commands stubbed)
reports syntax error and never reaches booti for this script. The prior LF
script and repaired script each reach booti once. This proves the artifact
parser failure; it is not a captured serial trace from the affected box.

The .cmd attribute now enforces LF even when Windows Git archives the commit.
Assembly checks source bytes and compiled legacy header/data CRCs and text.
Final package checks extract both script files from actual FAT with mtools;
the old FAT is rejected despite its valid container and uImage CRCs.

All 204 boot filesystem file contents were compared: only emmc_autoscript
and emmc_autoscript.cmd differ. The root filesystem remains byte-identical
(SHA-256 e7714dd3e0433d34c7307489f24226921ab6f828878d2d220e609a8f017758b1).
W102D again passes 26 capacity tests and matches the repaired W103D root/boot.

Invalid original hashes (do not use): W103D b7af1e18a1e0c2cb6bd3819064206fa032b29dc66c49445500ce3a5e3fd6b509;
W102D a4a4ba39120f439c207d175f7e3e5791b2a6f1140625ac23129e1bda5dd11542.
Evidence: workspace output/research/20260907-bootloop and delivery checks/boot-repair.
Release numbers must not increase without explicit user permission.
