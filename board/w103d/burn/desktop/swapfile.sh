#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail
dir=/var/lib/w103d
swap="$dir/swapfile"
install -d -m700 "$dir"
# This service owns exactly this file; never repurpose a pre-existing file.
if [[ ! -e "$swap" ]]; then
    available=$(df --output=avail -B1 "$dir" | tail -n1)
    (( available >= 3221225472 )) || { echo 'Less than 3 GiB free; keeping zram only.'; exit 0; }
    [[ $(findmnt -n -o FSTYPE -T "$dir") == ext4 ]] || { echo 'Expected ext4 for swapfile.'; exit 1; }
    tmp=$(mktemp "$dir/.swapfile.XXXXXX")
    trap 'rm -f -- "$tmp"' EXIT
    chmod 600 "$tmp"
    fallocate -l 2G "$tmp"
    mkswap "$tmp"
    sync "$tmp"
    mv "$tmp" "$swap"
    trap - EXIT
fi
[[ -f "$swap" && ! -L "$swap" && $(stat -c %s "$swap") == 2147483648 ]]
[[ $(blkid -p -s TYPE -o value "$swap") == swap ]]
chmod 600 "$swap"
if ! swapon --show=NAME --noheadings --raw | grep -Fxq "$swap"; then swapon -p 10 "$swap"; fi
