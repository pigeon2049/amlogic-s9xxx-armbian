#!/bin/bash
# The rebuild replaces the stock kernel and deletes its dpkg control files.
# Remove that stale registration only when no package-owned files/scripts
# remain; do not uninstall an actual installed kernel package.
set -euo pipefail
package=linux-image-current-meson64
if dpkg-query -W "$package" >/dev/null 2>&1; then
    if compgen -G "/var/lib/dpkg/info/$package.*" >/dev/null; then
        echo 'Stock kernel has control files; refusing metadata-only cleanup.' >&2
        exit 1
    fi
    test -d /usr/lib/modules/6.18.49-ophub
    dpkg --remove "$package"
fi
