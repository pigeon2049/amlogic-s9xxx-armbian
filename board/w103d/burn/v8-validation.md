# W103D v8 / W102D v4 complete desktop delivery

Date: 2026-09-08. The original filenames and delivery directories are
overwritten. Release numbers remain v8/v4 as requested.

| Image | Bytes | Current SHA-256 |
| --- | ---: | --- |
| W103D v8 | 6,065,238,080 | `f3cceb585d92a526dc65a8bc3798a387e947de04852915fd20516dada6e51b19` |
| W102D v4 | 6,065,242,176 | `531313c2616c54d7591536e731a7e998536d824087ca7511d772a0333c261d58` |

Source commits: W103D `9f799c88e7d52022a335425c348bd7cf14421b5d` (`w103d-burn-6.18`),
W102D `5fd8658ba72982037348e1f8b60672a813fec140` (`w102d-burn-6.18`). Source archives contain
these exact commits; this documentation-only follow-up records output hashes.

The complete desktop contract contains 103 explicit
packages, satisfied by 1560 installed packages and
Debian virtual providers. Added notification/XDG tools, Vulkan ICDs/tools,
file/archive/media utilities, GTK4/Qt5 input methods, viewers/thumbnails,
GTK appearance, wallet, SMB/exFAT, Discover/PackageKit, printing, KDE Connect,
LibreOffice with KDE integration and Simplified Chinese UI/offline help,
and Firefox Simplified Chinese. KDE translations are shipped by KDE packages.

Validation passed: explicit package/provider and Chinese resource checks,
dpkg audit and APT dependency check, actual ARM64 ordinary-user application
startup and Chinese LibreOffice PDF conversion, software Vulkan enumeration,
ordinary-user IPv4/IPv6 ping, BlueDevil Global configuration, original pairing
backport and board upgrade protection, exact wireless hashes and full
6.18.49-ophub ABI, boot FAT script LF/source/CRC, firmware/initramfs,
filesystems, container payload and sparse expansion checks.

QEMU virt clean first boot and root/armbian SSH pass on the new root.
QEMU directly loads the kernel and bypasses physical U-Boot; it does not
validate W103D/W102D hardware. W102D passes 26 capacity bootstrap cases;
its rootfs/bootfs are byte-identical to this tested W103D base.

PanVK is not enabled globally. The Vulkan runtime test selects Lavapipe
software rendering, not Mali-G31 GPU acceleration. Hardware Vulkan,
mouse startup reconnection, printers, network shares and W102D hardware
compatibility remain untested in this build. Scan packet loss is unresolved.
No kernel/module rebuild or physical flashing was performed.

Rootfs SHA-256: `0df21ee28bfc6dd0a27f0c162e5a64d8dd9219a05ec9d984c769157cd7401b0e`.
Bootfs SHA-256: `1072db34ebc8f9a711ef1f42ea4c12d925828dd59cb41de0334ca8faa182db23`.

All earlier hashes for these filenames are superseded. Current evidence:
`output/research/20260908-full-desktop-unlocked`, delivery `checks/full-desktop-unlocked` and
`checks/root-preparation`. Earlier git-lf-rebuild/boot-repair folders are
historical evidence. Build recipe: [v8-README.md](v8-README.md).
