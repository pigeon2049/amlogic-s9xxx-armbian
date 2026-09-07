# W103D v7 / W102D v3 offline release validation

Correction (2026-09-07): the original KDE check below used the wrong INI
group. Shipped BlueDevil 6.3.4 reads `Global`, whereas v7/v3 wrote `General`.
Those images do not implement the claimed explicit login-enable policy.
See [desktop-permissions-validation.md](desktop-permissions-validation.md)
for the corrected source, ping permissions and independent validation.
Original release artifacts remain unchanged.

Date: 2026-09-07. Prepared from the immutable clean W103D v6 root, with the
two already board-tested `6.18.49-ophub` modules and Bluetooth startup policy.
No kernel/module rebuild or live module reload was needed for this packaging.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| W103D_Armbian_26.8.1_6.18.49_KDE_v7.burn.img | 4699997344 | `646d0b58fc5f9fef22eaf29c8172fa8c2cc5c2ddcd0bb14808ac2ceb3929080b` |
| W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v3.burn.img | 4700001440 | `8ce56db945b27e48154355dc0aeea0bca621b8b17248285c2e653ced0a470943` |

The clean-root migration, repeated offline installation, desktop/account
checks, original BlueDevil pairing-backport verification and filesystem
checks passed. BlueZ AutoEnable, enabled service and KDE launchState=enable
are present for the default and future users. No Bluetooth bonds, captured
adapter identity, saved Bluetooth rfkill state or Wi-Fi profile is shipped.

Three native configuration regressions pass: changing the remembered-off
policy while preserving bond/device data and idempotence; accepting a clean
image while rejecting Remember; rejecting a captured rfkill snapshot.
These use the real configurator and offline systemctl, not Bluetooth hardware.

Module checks validated the exact decompressed hashes in
`wireless-modules.json`, full vermagic, required dependencies and SDIO alias.
Both older v6 modules were rejected despite matching `6.18.49-ophub` vermagic.
XZ and gzip recompressions of both correct modules passed. An invalid second
candidate was rejected before either target file changed. Metadata is checked
on decompressed bytes because the build host's kmod does not support gzip.

The assembler rejected stale-copy risk by requiring no MT7663S/mac80211 in
initramfs; this base satisfies that condition. Firmware, Image, DTB, module,
initramfs/uInitrd consistency, container integrity, every payload/VERIFY record,
sparse expansion, bootstrap init and logo checks passed for the final packages.

W102D additionally passed 26 ARM bootstrap cases (7 accepted capacities,
19 rejection cases). Its root and boot raw images match the W103D v7 base:

- rootfs SHA-256: `f9bd23c376554ba00c00b8660f474a30f3a4212639e99ff3005628f2e2597e4d`
- bootfs SHA-256: `0bc20fb59dbb5e527e5b77fb55363b31d1a53ee6d85a501e6f659308a1a947f4`

Only boot/recovery bootstrap payloads and their VERIFY records differ.
The W102D build rechecked the mounted base's actual modules, startup policy,
pairing backport and boot components rather than trusting reports alone.

Neither new container has been flashed or QEMU-booted in this follow-up.
Bluetooth mouse reconnection after a real boot of these packages remains
unverified, and W102D hardware compatibility is still a capacity trial.
The existing W103D module-pair hardware results are recorded in
[scan-rate-validation.md](../linux/scan-rate-validation.md); scanning packet
loss remains unresolved. The live board was inspected only during this
packaging follow-up; its configuration, pairing keys and running session
were not changed.
