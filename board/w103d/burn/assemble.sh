#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Assemble the W103D 6.18.52 production USB Burning Tool image
# (mainline U-Boot chainload). No board I/O.
#
# Verified production flow (board-tested 2026-09-20):
# - vendor DDR.USB / _aml_dtb / boot / recovery / dtbo / vbmeta / logo /
#   platform.conf pass through byte-identical (no bootstrap patching, no
#   logo rebuild; the box has eFuse secure-boot, FIP replacement is
#   impossible without the vendor key)
# - bootfs = base p1 contents + u-boot.ext (mainline, chainload) +
#   bootup.bmp (HDMI logo) + production emmc_autoscript (+.cmd)
# - uEnv.txt is written with the verified content below (do not trust the
#   base image's copy: LINUX/INITRD/FDT paths are W103D-specific)
set -euo pipefail
[[ $# == 6 ]] || { echo "Usage: $0 BASE.img.gz WORKDIR REFERENCE_UNPACKED TOOLS UBOOT_EXT BOOTUP_BMP" >&2; exit 2; }
baseimg=$(realpath "$1")
work=$(realpath -m "$2")
reference=$(realpath "$3")
tools=$(realpath "$4")
ubootext=$(realpath "$5")
bootupbmp=$(realpath "$6")
scripts=$(cd "$(dirname "$0")" && pwd)
board=$(dirname "$scripts")
[[ "$work" != / && "$work" != "$HOME" && "$work" != "$reference" ]]
mkdir -p "$work"/{payloads,checks,root,boot}
test ! -e "$work/payloads/image.cfg"
loop=''; bootloop=''
cleanup() {
    mountpoint -q "$work/base-boot" && umount "$work/base-boot" || true
    mountpoint -q "$work/root" && umount "$work/root" || true
    mountpoint -q "$work/boot" && umount "$work/boot" || true
    [[ -z "$bootloop" ]] || losetup -d "$bootloop"
    [[ -z "$loop" ]] || losetup -d "$loop"
}
trap cleanup EXIT
gzip -dc "$baseimg" > "$work/base.img"
loop=$(losetup --find --show --partscan --read-only "$work/base.img")
dd if="${loop}p2" of="$work/rootfs.raw" bs=4M status=none
e2label "$work/rootfs.raw" W103D_ROOT
mount -o loop "$work/rootfs.raw" "$work/root"
python3 "$scripts/sanitize_overlay_modes.py" "$work/root" --apply > "$work/checks/overlay-mode-fix.json"
truncate -s 1G "$work/bootfs.raw"
mkfs.vfat -F32 -n W103D_BOOT -i 103D6181 "$work/bootfs.raw" > "$work/checks/mkfs-boot.log"
bootloop=$(losetup --find --show "$work/bootfs.raw")
mount "$bootloop" "$work/boot"
mkdir -p "$work/base-boot"
mount -o ro "${loop}p1" "$work/base-boot"
cp -r "$work/base-boot/." "$work/boot/"
umount "$work/base-boot"
# Chainload U-Boot (mainline) + HDMI logo + production autoscript.
cp "$ubootext" "$work/boot/u-boot.ext"
cp "$bootupbmp" "$work/boot/bootup.bmp"
mkimage -A arm64 -O linux -T script -C none -n 'W103D mainline U-Boot' -d "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript" > "$work/checks/bootscript.log"
cp "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript.cmd"
cat > "$work/boot/uEnv.txt" <<'EOF'
LINUX=/zImage
INITRD=/ramdisk-w103d.img
FDT=/dtb-w103d/meson-g12a-w103d.dtb
APPEND=root=LABEL=W103D_ROOT rw rootwait rootfstype=ext4 console=ttyAML0,115200n8 console=tty0 net.ifnames=0 fsck.repair=yes
EOF
cat > "$work/root/etc/fstab" <<'EOF'
LABEL=W103D_ROOT / ext4 defaults,noatime,errors=remount-ro 0 1
LABEL=W103D_BOOT /boot vfat defaults 0 2
tmpfs /tmp tmpfs defaults,nosuid 0 0
EOF
echo no > "$work/root/root/.no_rootfs_resize"
sed -i "s/DISK_TYPE='usb'/DISK_TYPE='emmc'/" "$work/root/etc/ophub-release"
install -D -m755 "$scripts/resize-rootfs.sh" "$work/root/usr/local/sbin/w103d-resize-rootfs"
install -D -m644 "$scripts/resize-rootfs.service" "$work/root/etc/systemd/system/w103d-resize-rootfs.service"
mkdir -p "$work/root/etc/systemd/system/multi-user.target.wants"
ln -s ../w103d-resize-rootfs.service "$work/root/etc/systemd/system/multi-user.target.wants/w103d-resize-rootfs.service"
# Rebuild input is a pristine official image. Drop per-image machine identity.
: > "$work/root/etc/machine-id"
rm -f "$work/root/var/lib/dbus/machine-id"
ln -s /etc/machine-id "$work/root/var/lib/dbus/machine-id"
find "$work/root/etc/ssh" -maxdepth 1 -name 'ssh_host_*' -type f -delete
install -D -m644 "$scripts/ssh-hostkeys.conf" "$work/root/etc/systemd/system/ssh.service.d/10-w103d-hostkeys.conf"
sed -i 's/^OPENSSHD_REGENERATE_HOST_KEYS=.*/OPENSSHD_REGENERATE_HOST_KEYS=false/' "$work/root/etc/default/armbian-firstrun"
python3 "$board/validation/verify_image.py" --rootfs "$work/root" --bootfs "$work/boot" --release 6.18.52-ophub | tee "$work/checks/components.log"
sync
umount "$work/root" "$work/boot"
losetup -d "$bootloop";bootloop=''
losetup -d "$loop";loop=''
e2fsck -fn "$work/rootfs.raw" > "$work/checks/rootfs-fsck.log" 2>&1
fsck.vfat -n "$work/bootfs.raw" > "$work/checks/bootfs-fsck.log" 2>&1
python3 "$scripts/raw_to_sparse.py" "$work/bootfs.raw" "$work/payloads/system.PARTITION"
python3 "$scripts/raw_to_sparse.py" "$work/rootfs.raw" "$work/payloads/data.PARTITION"
# Vendor boot chain passes through untouched (secure-boot: no re-signing).
for n in DDR.USB _aml_dtb.PARTITION boot.PARTITION recovery.PARTITION dtbo.PARTITION vbmeta.PARTITION logo.PARTITION platform.conf; do
    cp "$reference/$n" "$work/payloads/$n"
done
cat > "$work/payloads/image.cfg" <<'EOF'
[LIST_NORMAL]
file="DDR.USB" main_type="USB" sub_type="DDR" file_type="normal"
file="DDR.USB" main_type="USB" sub_type="UBOOT" file_type="normal"
file="_aml_dtb.PARTITION" main_type="dtb" sub_type="meson1" file_type="normal"
file="platform.conf" main_type="conf" sub_type="platform" file_type="normal"
[LIST_VERIFY]
file="_aml_dtb.PARTITION" main_type="PARTITION" sub_type="_aml_dtb" file_type="normal"
file="boot.PARTITION" main_type="PARTITION" sub_type="boot" file_type="normal"
file="recovery.PARTITION" main_type="PARTITION" sub_type="recovery" file_type="normal"
file="dtbo.PARTITION" main_type="PARTITION" sub_type="dtbo" file_type="normal"
file="vbmeta.PARTITION" main_type="PARTITION" sub_type="vbmeta" file_type="normal"
file="logo.PARTITION" main_type="PARTITION" sub_type="logo" file_type="normal"
file="system.PARTITION" main_type="PARTITION" sub_type="system" file_type="sparse"
file="data.PARTITION" main_type="PARTITION" sub_type="data" file_type="sparse"
file="DDR.USB" main_type="PARTITION" sub_type="bootloader" file_type="normal"
EOF
name=W103D_Armbian_26.8.1_6.18.52_Server_MainlineUboot.burn.img
"$tools/aml_image_v2_packer_new" -r "$work/payloads/image.cfg" "$work/payloads" "$work/$name" > "$work/checks/pack.log" 2>&1
"$tools/aml_image_v2_packer_new" -c "$work/$name" > "$work/checks/container-integrity.log" 2>&1
sha256sum "$work/$name" > "$work/$name.sha256"
echo "$work/$name"
