# W103D v8 / W102D v4 release validation

Date: 2026-09-07. Built from immutable clean v6 using committed source:

- W103D `w103d-burn-6.18`: `ebc733891691d53e8ae5094bf63445d6a40fe1b8`.
- W102D `w102d-burn-6.18`: `879aa3429fd6f39d6cc52bec4c2c1df52a17ed4c`.

The source snapshots are included in each delivery. Later documentation-only
commits record the results and do not change the inputs used for these images.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| W103D_Armbian_26.8.1_6.18.49_KDE_v8.burn.img | 4698948768 | `b7af1e18a1e0c2cb6bd3819064206fa032b29dc66c49445500ce3a5e3fd6b509` |
| W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v4.burn.img | 4698952864 | `a4a4ba39120f439c207d175f7e3e5791b2a6f1140625ac23129e1bda5dd11542` |

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

These are offline and QEMU user-mode checks, not full guest boots or hardware
flashes. Mouse reconnection after real startup remains unverified. Existing
scan packet loss is not addressed. Original v7/v3 delivery files are retained.

Windows deliveries:

- `output/releases/W103D_6.18.49_KDE_USB_Burning_v8/`
- `w102d/output/W102D_6.18.49_KDE_16GB_USB_Burning_v4/`

Each contains the burn image, SHA-256 sidecar, manifest, instructions, checks
and source archive. Build recipe: [v8-README.md](v8-README.md).
