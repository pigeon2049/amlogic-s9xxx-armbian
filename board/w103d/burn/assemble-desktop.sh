#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Reuse the validated bootstrap/layout; replace only clean root and boot FAT.
set -euo pipefail
[[ $# == 4 ]] || { echo "Usage: $0 SERVER_ASSEMBLY CLEAN_DESKTOP_ROOT.raw WORKDIR TOOLS" >&2; exit 2; }
base=$(realpath "$1"); rootimg=$(realpath "$2"); work=$(realpath -m "$3"); tools=$(realpath "$4")
scripts=$(cd "$(dirname "$0")" && pwd)
test "$work" != "$base"
test ! -e "$work/payloads"
mkdir -p "$work"/{payloads,bootstrap,checks,root,boot}
cp --reflink=auto --sparse=always "$rootimg" "$work/rootfs.raw"
cp --reflink=auto --sparse=always "$base/bootfs.raw" "$work/bootfs.raw"
cp "$base/bootstrap/init" "$work/bootstrap/init"
for name in DDR.USB _aml_dtb.PARTITION platform.conf boot.PARTITION recovery.PARTITION dtbo.PARTITION vbmeta.PARTITION logo.PARTITION image.cfg; do
    cp "$base/payloads/$name" "$work/payloads/$name"
done
cleanup() {
    mountpoint -q "$work/root" && umount "$work/root" || true
    mountpoint -q "$work/boot" && umount "$work/boot" || true
}
trap cleanup EXIT
mount -o loop,ro "$work/rootfs.raw" "$work/root"
mount -o loop "$work/bootfs.raw" "$work/boot"
mkimage -A arm -O linux -T script -C none -n 'W103D 6.18 eMMC' -d "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript" > "$work/checks/bootscript.log"
cp "$scripts/emmc_autoscript.cmd" "$work/boot/emmc_autoscript.cmd"
python3 "$scripts/../validation/verify_image.py" --rootfs "$work/root" --bootfs "$work/boot" --release 6.18.49-ophub > "$work/checks/components.log"
# This recipe loads the Wi-Fi driver from the root filesystem. Refuse a
# stale embedded copy instead of silently booting an older scan implementation.
lsinitramfs "$work/boot/initrd.img-6.18.49-ophub" > "$work/checks/initramfs-files.txt"
if grep -Eq '(^|/)mt7663s\.ko(\.(xz|zst|gz))?$' "$work/checks/initramfs-files.txt"; then
    echo 'Regenerate initramfs before packaging an embedded MT7663S module.' >&2
    exit 1
fi
python3 "$scripts/desktop/verify-root.py" "$work/root" > "$work/checks/desktop.json"
python3 "$scripts/../fixes/bluedevil/verify-root.py" "$work/root" > "$work/checks/bluedevil.json"
sync
umount "$work/root" "$work/boot"
e2fsck -fn "$work/rootfs.raw" > "$work/checks/rootfs-fsck.log" 2>&1
zerofree "$work/rootfs.raw"
fsck.vfat -n "$work/bootfs.raw" > "$work/checks/bootfs-fsck.log" 2>&1
python3 "$scripts/raw_to_sparse.py" "$work/bootfs.raw" "$work/payloads/system.PARTITION"
python3 "$scripts/raw_to_sparse.py" "$work/rootfs.raw" "$work/payloads/data.PARTITION"
name=W103D_Armbian_26.8.1_6.18.49_KDE_v6.burn.img
"$tools/aml_image_v2_packer_new" -r "$work/payloads/image.cfg" "$work/payloads" "$work/$name" > "$work/checks/pack.log" 2>&1
"$tools/aml_image_v2_packer_new" -c "$work/$name" > "$work/checks/container-integrity.log" 2>&1
sha256sum "$work/$name" > "$work/$name.sha256"
echo "$work/$name"
