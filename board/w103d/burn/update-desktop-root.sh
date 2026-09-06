#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Update a mounted clean v3 root with a separately built and tested module.
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 MOUNTED_CLEAN_ROOT TESTED_MT7663S.ko" >&2; exit 2; }
root=$(realpath "$1"); module=$(realpath "$2")
scripts=$(cd "$(dirname "$0")" && pwd)
release=6.18.49-ophub
test "$root" != /
mountpoint -q "$root"
test "$(cat "$root/etc/hostname")" = armbian
test "$(modinfo -F vermagic "$module" | awk '{print $1}')" = "$release"
modinfo -F alias "$module" | grep -Fxq 'sdio:c*v037Ad7603*'
depends=,$(modinfo -F depends "$module"),
for name in mt76-connac-lib btmtksdio mt7663-usb-sdio-common mt7615-common mt76-sdio mt76 mac80211 cfg80211; do
    [[ "$depends" == *",$name,"* ]]
done
mapfile -t existing < <(find "$root/usr/lib/modules/$release" -type f -name 'mt7663s.ko*')
test "${#existing[@]}" = 1
test "${existing[0]##*/}" = mt7663s.ko
install -m644 "$module" "${existing[0]}"
depmod -b "$root" "$release"
install -D -m755 "$scripts/desktop/performance.sh" "$root/usr/local/sbin/w103d-performance"
install -D -m644 "$scripts/desktop/performance.service" "$root/etc/systemd/system/w103d-performance.service"
install -D -m644 "$scripts/desktop/cpufrequtils" "$root/etc/default/cpufrequtils"
systemctl --root="$root" enable w103d-performance.service
python3 "$scripts/desktop/protect-upgrades.py" "$root"
echo 'Updated the clean root with the tested scan driver and CPU policy.'
