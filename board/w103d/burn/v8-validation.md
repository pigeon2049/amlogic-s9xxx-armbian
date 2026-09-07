# W103D v8 / W102D v4 full desktop build — replacement status

Date: 2026-09-08. Version numbers and final filenames are unchanged.

W102D v4 has been replaced successfully. W103D v8 has been generated and
verified, but Windows denied replacing its original image while USB_Burning_Tool
was running. The new W103D bytes are staged in the original directory as
`W103D_Armbian_26.8.1_6.18.49_KDE_v8.burn.img.partial`. Do not confuse this with the old final .img file.

| Generated image | Bytes | New SHA-256 | Delivery |
| --- | ---: | --- | --- |
| W103D v8 | 6065238080 | `266c6d6e5e504b25518e6d8d25d1d489a40391335536456f436fe29b83e22539` | Verified .partial; final replacement pending |
| W102D v4 | 6065242176 | `e62d10f584205ac02473b73e93c08c988e848b1fdec9a529f38ee890293bccf7` | Original same-name .img replaced |

The currently locked W103D final .img and top-level manifest/sha256/source
still describe the older image: `1654cff9c9a807aa8706ee64d98b9bba180059ea9d107a9fb5b20ed0a13b9f2e`.
They will be updated together after the file is released.

New build source commits: W103D `9f799c88e7d52022a335425c348bd7cf14421b5d` and
W102D `5fd8658ba72982037348e1f8b60672a813fec140` on their respective burn-6.18 branches.
Both code commits are pushed. Documentation-only follow-ups record this status.

The new roots include all audited desktop and optional packages, complete
LibreOffice with KDE integration, Simplified Chinese UI/offline help,
Java/report support, compatible fonts and Chinese Firefox. There are 1560
installed packages (367 added), with no existing package upgrade or removal.

Passed: explicit packages/providers and Chinese resources, APT/dpkg checks,
actual ARM64 ordinary-user application startup and Chinese PDF export,
Lavapipe software Vulkan enumeration, ping/sysctl and BlueDevil Global config,
pairing backport and board package protection, exact module hashes/full
6.18.49-ophub ABI, firmware/kernel/DTB/initramfs, FAT script LF/source/CRC,
filesystems, containers, payload verification and sparse expansion checks.
The new W103D root passes QEMU virt startup and root/armbian SSH. W102D shares
its identical rootfs/bootfs and passes all 26 capacity bootstrap cases.

QEMU bypasses physical U-Boot and is not a board flash test. Hardware Vulkan,
mouse reconnection and external peripheral functions remain untested.
PanVK is not enabled globally; KWin retains the tested Panfrost GLES backend.
No kernel or module rebuild. Existing scan packet loss remains unresolved.

Current evidence: `output/research/20260908-full-desktop` and new build checks.
Finish W103D after closing the burning tool using the staged verified image;
update the manifest, source archive, instructions and this status together.
