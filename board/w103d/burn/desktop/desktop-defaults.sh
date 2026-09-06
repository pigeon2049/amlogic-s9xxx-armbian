#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# One-time layout for the factory account. Preserve later user customization.
set -eu
test "$(id -un)" = armbian || exit 0
marker="$HOME/.local/state/w103d-desktop-v2"
test ! -f "$marker" || exit 0
for attempt in $(seq 1 30); do
    if qdbus6 org.kde.plasmashell /PlasmaShell >/dev/null 2>&1; then break; fi
    sleep 1
done
plasma-apply-colorscheme Moe
plasma-apply-desktoptheme Moe
kwriteconfig6 --file kdeglobals --group Icons --key Theme Colloid
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat /usr/share/w103d/desktop-layout.js)"
mkdir -p "$(dirname "$marker")"
touch "$marker"
