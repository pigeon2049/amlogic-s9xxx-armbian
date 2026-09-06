#!/bin/sh
set -eu
test ! -e /var/lib/w103d/rootfs-expanded || exit 0
rootdev=$(findmnt -n -o SOURCE /)
test "$(blkid -s LABEL -o value "$rootdev")" = W103D_ROOT
resize2fs "$rootdev"
mkdir -p /var/lib/w103d
touch /var/lib/w103d/rootfs-expanded
