# KDE v5 upgrade-protection validation (2026-09-06)

- Image: `W103D_Armbian_26.8.1_6.18.49_KDE_v5.burn.img`
- Bytes: `4646520176`
- SHA-256: `d4ceaedff93166164831447fc67c560e67e65579944a8e2ba42e7edc7c3828e0`
- Runtime remains `6.18.49-ophub`; no driver or kernel was rebuilt for v5.
- Clean origin: v4 plus the board-package holds and negative APT priority.

In an isolated QEMU virt copy, APT installed seven userspace updates, including
26.8.3 base-files. The four installed board packages stayed at 26.8.1.
Every original boot file, board identity, MT7663S module and tested firmware
retained its SHA-256. APT exited successfully and dpkg reported no unfinished
configuration. After a normal shutdown and boot, the kernel release, hashes,
W103D DTB and identity were checked again; root and armbian SSH logins passed.

The ordinary upgrade and dist-upgrade plans both excluded board replacements.
Removing only the DTB hold still left the negative pin effective. Installing
the generic `linux-image-current-meson64` through normal APT selection was
rejected for lack of a candidate. The installer also passed repeat execution.

The current configng armbian-config download returned 404 in the unprotected
comparison. Only the test copy held that unrelated tool; the shipping image
holds exactly the four board packages, leaving the configurator and normal
userspace updates available. This is not a claim that every repository package
was successfully upgraded.

The final container passed component/ABI, firmware, desktop/identity, ext4/FAT,
payload/VERIFY, expanded sparse and logo checks. A separate snapshot of its
clean filesystems generated fresh SSH host keys and accepted both default
accounts without the first-login wizard. The upgraded test filesystem and its
logs/identities were not used as the shipping root.

QEMU virt does not emulate the board's original U-Boot, Wi-Fi or HDMI. This v5
container has not been flashed to hardware. The protection covers normal APT
resolution; it does not recover an already deleted DTB or prevent deliberate
root overrides, direct dpkg installation or manual boot-file changes.
