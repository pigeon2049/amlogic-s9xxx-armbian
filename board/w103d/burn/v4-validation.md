# KDE v4 package validation (2026-09-06)

- Image: `W103D_Armbian_26.8.1_6.18.49_KDE_v4.burn.img`
- Bytes: `4643374448`
- SHA-256: `7d4c245b732d68d8ba7ac1e5c010b0222f3c6d770383a567733e485bb94a7297`
- Target: the tested 32 GB W103D, 60,620,800 eMMC sectors.
- Runtime: `6.18.49-ophub`; bootstrap-only kernel remains the reference 4.9.113.
- Root origin: a copy of the clean v3 image, never the test board filesystem.
- MT7663S SHA-256: `1f0f1456c311423dd7f2eb189c805a689515d3cb3a93f810cd74cd995df78737`.
- Previous v3 container SHA-256: `e09e7d3faffffa0c0b928d0388fd6249fc15d10836922a6b222fcaceef5ee809`.

The module is the exact artifact previously loaded and reboot-tested on the
board. Twenty full-channel scans across both bands preserved association;
concurrent scanning and 512 MiB transfers in each direction completed.
Scanning still affects packet loss, latency and throughput. The CPU policy
uses the existing 1.8 GHz OPP with thermal protection; the earlier three-minute
four-core board test peaked at 70.7 C. No KDE scan timer was modified.

Package checks passed: exact module vermagic/dependencies/alias, matched
Image/DTB/initramfs/firmware, absent embedded MT7663S initramfs copy, clean
desktop/account defaults, no Wi-Fi profiles or SSH/wallet identities, ext4
and FAT integrity, vendor container verification, every payload and VERIFY
digest, expanded sparse partition hashes and the supplied boot logo.

QEMU virt booted a snapshot of the final raw filesystems with the matching
kernel, generated fresh SSH host keys, and accepted both `root / 1234` and
`armbian / 1234` over SSH without the first-login wizard. QEMU does not emulate
W103D Wi-Fi, HDMI, thermal behavior or USB flashing. The bootstrap's separate
QEMU-user tests also passed provisioning, repeat execution and rejection of
bad EPT, environment CRC and root signatures without writes.

The new v4 container has not been flashed to the board in this release run.
The board was not reachable for a fresh SSH check; the hardware evidence is
from the immediately preceding driver/configuration tests. The local release
directory includes build inputs, source snapshot, checks and flashing notes.
