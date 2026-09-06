#!/bin/bash
# Make a clean release root from v5; never use the compiler or live-board root.
set -euo pipefail
[[ $# == 3 ]] || { echo "Usage: $0 CLEAN_V5_ROOT.raw NEW_WORKDIR TESTED_BACKPORT.deb" >&2; exit 2; }
base=$(realpath "$1"); work=$(realpath -m "$2"); deb=$(realpath "$3")
scripts=$(cd "$(dirname "$0")" && pwd)
test ! -e "$work"
mkdir -p "$work/root" "$work/checks"
cp --reflink=auto --sparse=always "$base" "$work/rootfs.raw"
cleanup() { mountpoint -q "$work/root" && umount "$work/root" || true; }
trap cleanup EXIT
mount -o loop "$work/rootfs.raw" "$work/root"
python3 "$scripts/desktop/verify-root.py" "$work/root" > "$work/checks/baseline-desktop.json"
bash "$scripts/../fixes/bluedevil/install-image.sh" "$work/root" "$deb" > "$work/checks/install.log" 2>&1
# Repeat installation to exercise the idempotent offline update path.
bash "$scripts/../fixes/bluedevil/install-image.sh" "$work/root" "$deb" > "$work/checks/install-repeat.log" 2>&1
python3 "$scripts/../fixes/bluedevil/verify-root.py" "$work/root" > "$work/checks/bluedevil.json"
python3 "$scripts/desktop/verify-root.py" "$work/root" > "$work/checks/desktop.json"
sync
umount "$work/root"
e2fsck -fn "$work/rootfs.raw" > "$work/checks/rootfs-fsck.log" 2>&1
