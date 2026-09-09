# W103D / W102D unified image delivery

Date: 2026-09-10. Both models use the same capacity-adaptive bootstrap and
byte-identical firmware. Original W103D v8 / W102D v4 filenames and delivery
directories have been overwritten as compatibility entries; no new version.

| Compatibility filename | Bytes | SHA-256 |
| --- | ---: | --- |
| W103D_Armbian_26.8.1_6.18.49_KDE_v8.burn.img | 6065242176 | `c793e6278c2bce85070cf0adf0d5b66309c4c501fa36e37ffab6b8e200f38bd3` |
| W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v4.burn.img | 6065242176 | `c793e6278c2bce85070cf0adf0d5b66309c4c501fa36e37ffab6b8e200f38bd3` |

Build commits: W103D `5a4b100ea5a43acf70f70eb716a658ab53351baf`, W102D
`f6cd6ccad6d91e152217b1e46f0c6839ecdb0e5e`. These are the commits in the actual build
archives; subsequent documentation commits record delivery results.

The failure was a hardcoded 60,620,800-sector requirement rejecting a
Y2P032 W103D with 61,071,360 sectors before configuring Armbian. Both nominal
capacity whitelists are removed. The shared bootstrap verifies ext4 fits,
cross-checks measured capacity with EPT and constructs the MBR from it.
The root partition extends to the measured device end. Details, retained
MBR format limits and reproduction: [unified-capacity.md](unified-capacity.md).

Both source-entry test runs passed all 43 ARM provisioning cases. An extra
fixture using the affected unit's actual EPT and shipping ext4 superblock
successfully configured a 57,069,568-sector root partition starting at
4,001,792, ending at 61,071,360 exclusive. These were host sparse fixtures,
not on-device writes or a physical boot test.

Actual packed payload/VERIFY hashes, Android boot initramfs and digest,
FAT script LF/source/legacy CRC, sparse expansion and CRC, root/boot
filesystems, desktop/firmware, exact module hashes and full 6.18.49-ophub
ABI checks passed. Forced CRLF checkout/archive tests passed for both Git
branches. Both actual image files were compared byte-for-byte and their
delivery SHA-256 was verified after replacing the original filenames.

Relative to the previous W103D image, only boot/recovery provisioning
payloads and their VERIFY records changed. Both DTBs, project LED GPIO,
DDR/U-Boot, Logo, kernel/modules, rootfs and FAT are unchanged. W102D's
legacy build entry produces zero payload differences from the common image.

Rootfs SHA-256: `0df21ee28bfc6dd0a27f0c162e5a64d8dd9219a05ec9d984c769157cd7401b0e`.
Bootfs SHA-256: `1072db34ebc8f9a711ef1f42ea4c12d925828dd59cb41de0334ca8faa182db23`.
Init SHA-256: `af05576e7759dfeff75cf404ca012defcd90ea63b3527ee1817e923250e3c339`.

The current 8 GiB root requires 20,779,008 sectors total, including the
front reservation. This is a fit calculation, not a nominal-capacity list.

No physical device was flashed in this build. Both models still need a
physical first-start/cold-boot check for this unified image. Previous QEMU
system-start/SSH evidence belongs to the byte-identical root and FAT and is
retained under checks-history; it is not a test of this new physical bootstrap.
Existing Bluetooth reconnection and wireless scan-loss limitations remain.

Current evidence: output/research/20260910-unified-capacity and each delivery's
checks/unified-capacity. Previous same-filename hashes are superseded.
Deliveries include updated manifests, SHA-256 sidecars, source archives,
instructions and current checks; prior evidence remains in checks-history.
