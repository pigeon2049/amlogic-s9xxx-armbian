# W103D v8 / W102D v4 current delivery

Date: 2026-09-07. Rebuilt after repository-wide LF enforcement and confirmation
that the burning tool was closed. Both original delivery paths are overwritten;
release names and version numbers are unchanged.

| Image | Bytes | Current SHA-256 |
| --- | ---: | --- |
| W103D v8 | 4699997344 | `1654cff9c9a807aa8706ee64d98b9bba180059ea9d107a9fb5b20ed0a13b9f2e` |
| W102D v4 | 4700001440 | `070eec9c40bf6fc05db55b633b9d8d4b34288e352da9de24fe4fb9a22c770ed5` |

Build source commits:

- W103D: `ae8825dcf090026e078d1c1f7e62c8da8da25cc4` on `w103d-burn-6.18`.
- W102D: `3be9ca2dba087d57837ef79f4dbc3cc2a09be760` on `w102d-burn-6.18`.

The source archives are exact snapshots of these commits. Documentation-only
follow-up commits record the output hashes without changing build inputs.

A new clean desktop root was prepared from immutable v6 with current source.
BlueDevil Global startup policy, ordinary-user IPv4/IPv6 ping and repeated
systemd-sysctl application pass. Real ARM64 KDE configuration reads pass.
The actual FAT script is LF and matches the source, with valid legacy CRCs.
Both container/payload/VERIFY/sparse, firmware, kernel/DTB/initramfs, exact
module hashes/full 6.18.49-ophub ABI, pairing package and filesystem checks pass.

The newly generated W103D root passes QEMU virt clean startup, SSH host-key
generation and both root/armbian SSH logins using temporary snapshots.
The test directly loads the kernel, bypasses physical U-Boot and does not
emulate W103D hardware. W102D passes all 26 capacity bootstrap cases and has
identical rootfs/bootfs to this tested W103D base; only boot/recovery provisioning
payloads and their VERIFY items differ.

No kernel was rebuilt and no modules were hot-reloaded. Neither new image
has been physically flashed in this run. Mouse startup reconnection and
W102D hardware compatibility remain unverified; scan packet loss is unresolved.

Rootfs SHA-256: `3e5a2f977e974d3d7509b42185bf6aae2960fb48d3f966f4380c0c7b527b15c1`.
Bootfs SHA-256: `e85945ecce7adfc2ec5246b344309205dcd13f57c63ff63b1c8e27edbdab49ff`.

## Prior boot-loop defect

The first v8/v4 archive converted the eMMC .cmd script from LF to CRLF under
Windows Git. The vendor-family Hush parser reproduced syntax error with no
booti call. Explicit .cmd LF attributes and actual packed-script checks fixed
that defect; root-level text/auto LF attributes now protect the entire repo,
with Windows/Linux checkout/archive byte-identity CI.

All previously recorded hashes for these same filenames are superseded by
the table above, including the first defective hashes beginning b7af1e18 /
a4a4ba39 and the interim repair hashes cd87d6be / 915a5419.
Historical diagnosis: workspace output/research/20260907-bootloop.
Current build evidence: output/research/20260907-git-lf-rebuild.

Deliveries contain the image, SHA-256 sidecar, manifest, instructions, source
archive and checks. Recipe: [v8-README.md](v8-README.md).
