#!/bin/bash
# Prepare v7 from an immutable, clean pairing-fixed v6 root.
set -euo pipefail
[[ $# == 4 ]] || { echo "Usage: $0 CLEAN_V6_ROOT.raw NEW_WORKDIR TESTED_MT7663S.ko TESTED_MAC80211.ko" >&2; exit 2; }
base=$(realpath "$1"); work=$(realpath -m "$2")
scripts=$(cd "$(dirname "$0")" && pwd)
test ! -e "$work"
mkdir -p "$work/root" "$work/checks"
cp --reflink=auto --sparse=always "$base" "$work/rootfs.raw"
cleanup() { mountpoint -q "$work/root" && umount "$work/root" || true; }
trap cleanup EXIT
mount -o loop "$work/rootfs.raw" "$work/root"
python3 "$scripts/desktop/verify-root.py" "$work/root" > "$work/checks/baseline-desktop.json"
python3 "$scripts/../fixes/bluedevil/verify-root.py" "$work/root" > "$work/checks/baseline-bluedevil.json"
bash "$scripts/update-desktop-root.sh" "$work/root" "$3" "$4" > "$work/checks/update.log" 2>&1
python3 "$scripts/desktop/verify-root.py" "$work/root" > "$work/checks/desktop.json"
python3 "$scripts/desktop/verify-bluetooth.py" "$work/root" > "$work/checks/bluetooth-startup.json"
python3 "$scripts/wireless_modules.py" "$work/root" > "$work/checks/wireless-modules.json"
sync
umount "$work/root"
e2fsck -fn "$work/rootfs.raw" > "$work/checks/rootfs-fsck.log" 2>&1
