#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Assemble a W103D-specific experimental USB Burning Tool image. No board I/O.
set -euo pipefail
[[ $# == 4 ]] || { echo "Usage: $0 BASE.img.gz WORKDIR REFERENCE_UNPACKED TOOLS" >&2; exit 2; }
baseimg=$(realpath "$1")
work=$(realpath -m "$2")
reference=$(realpath "$3")
tools=$(realpath "$4")
scripts=$(cd "$(dirname "$0")" && pwd)
board=$(dirname "$scripts")
[[ "$work" != / && "$work" != "$HOME" && "$work" != "$reference" ]]
mkdir -p "$work"/{payloads,checks,root,boot,bootstrap}
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
mkimage -A arm -O linux -T script -C none -n 'W103D 6.18 eMMC' -d "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript" > "$work/checks/bootscript.log"
cp "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript.cmd"
cat > "$work/boot/uEnv.txt" <<'EOF'
LINUX=/zImage
INITRD=/uInitrd
FDT=/dtb/amlogic/meson-g12a-w103d.dtb
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
python3 "$board/validation/verify_image.py" --rootfs "$work/root" --bootfs "$work/boot" --release 6.18.49-ophub | tee "$work/checks/components.log"
find "$work/root/etc/NetworkManager/system-connections" "$work/root/etc/wpa_supplicant" -type f -printf '%p\n' 2>/dev/null > "$work/checks/network-profile-files.txt" || true
find "$work/root/root" -maxdepth 2 -type f -printf '%P\n' > "$work/checks/root-home-files.txt"
sync
umount "$work/root" "$work/boot"
losetup -d "$bootloop";bootloop=''
losetup -d "$loop";loop=''
e2fsck -fn "$work/rootfs.raw" > "$work/checks/rootfs-fsck.log" 2>&1
fsck.vfat -n "$work/bootfs.raw" > "$work/checks/bootfs-fsck.log" 2>&1
clang --target=arm-linux-gnueabi -march=armv7-a -marm -Os -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -static -fuse-ld=lld -Wl,--build-id=none -Wl,-e,_start "$scripts/bootstrap.c" -o "$work/bootstrap/init"
python3 "$scripts/make_bootstrap.py" "$reference/boot.PARTITION" "$work/bootstrap/init" "$work/payloads/boot.PARTITION"
python3 "$scripts/raw_to_sparse.py" "$work/bootfs.raw" "$work/payloads/system.PARTITION"
python3 "$scripts/raw_to_sparse.py" "$work/rootfs.raw" "$work/payloads/data.PARTITION"
cp "$reference/DDR.USB" "$reference/_aml_dtb.PARTITION" "$reference/platform.conf" "$reference/dtbo.PARTITION" "$reference/vbmeta.PARTITION" "$work/payloads/"
mkdir -p "$work/logo-input"
cp /mnt/d/w103d/preserved/assets/boot-logo/tieba-dog-head-bootup-1280x720.bmp "$work/logo-input/bootup.bmp"
LD_LIBRARY_PATH="$tools/lib64" "$tools/logo_img_packer" -r "$work/logo-input" "$work/payloads/logo.PARTITION"
# Recovery also runs the provisioning helper, never an Android factory reset.
cp "$work/payloads/boot.PARTITION" "$work/payloads/recovery.PARTITION"
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
name=W103D_Armbian_26.8.1_6.18.49_BOOTSTRAP_v1_UNTESTED.burn.img
"$tools/aml_image_v2_packer_new" -r "$work/payloads/image.cfg" "$work/payloads" "$work/$name" > "$work/checks/pack.log" 2>&1
"$tools/aml_image_v2_packer_new" -c "$work/$name" > "$work/checks/container-integrity.log" 2>&1
sha256sum "$work/$name" > "$work/$name.sha256"
echo "$work/$name"
