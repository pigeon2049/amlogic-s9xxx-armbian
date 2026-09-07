#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Update an offline clean root with both tested wireless fixes and startup policy.
set -euo pipefail
[[ $# == 3 ]] || { echo "Usage: $0 MOUNTED_CLEAN_ROOT TESTED_MT7663S.ko TESTED_MAC80211.ko" >&2; exit 2; }
root=$(realpath "$1")
scripts=$(cd "$(dirname "$0")" && pwd)
release=6.18.49-ophub
test "$root" != /
mountpoint -q "$root"
test "$(cat "$root/etc/hostname")" = armbian
python3 "$scripts/wireless_modules.py" "$root" --install "$2" "$3"
depmod -b "$root" "$release"
python3 "$scripts/desktop/configure-bluetooth.py" "$root"
python3 "$scripts/desktop/verify-bluetooth.py" "$root"
install -D -m755 "$scripts/desktop/performance.sh" "$root/usr/local/sbin/w103d-performance"
install -D -m644 "$scripts/desktop/performance.service" "$root/etc/systemd/system/w103d-performance.service"
install -D -m644 "$scripts/desktop/cpufrequtils" "$root/etc/default/cpufrequtils"
systemctl --root="$root" enable w103d-performance.service
python3 "$scripts/desktop/protect-upgrades.py" "$root"
echo 'Updated both wireless modules, Bluetooth startup and CPU policy.'
