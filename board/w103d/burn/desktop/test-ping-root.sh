#!/bin/bash
# Verify real ARM64 ordinary-user ping in private network/mount namespaces.
# Requires root, a mounted prepared root, and registered aarch64 binfmt/QEMU.
set -euo pipefail
[[ $# == 1 ]] || { echo "Usage: $0 MOUNTED_ROOT" >&2; exit 2; }
root=$(realpath "$1")
test "$root" != /
mountpoint -q "$root"
exec unshare --mount --net bash -s -- "$root" <<'TEST'
set -euo pipefail
root=$1
mount --make-rprivate /
mount -t proc proc "$root/proc"
trap 'umount "$root/proc"' EXIT
ip link set lo up
sysctl -w net.ipv4.ping_group_range='1 0'
echo 'Before: actual ARM64 ping as uid/gid 1000 without CAP_NET_RAW'
set +e
setpriv --bounding-set=-net_raw chroot --userspec=1000:1000 "$root" /usr/bin/ping -4 -n -c 1 -W 2 127.0.0.1
before=$?
set -e
test "$before" -ne 0
echo "before_exit=$before"
# Apply the real image's complete sysctl.d ordering for this key only.
chroot "$root" /usr/lib/systemd/systemd-sysctl --prefix=/net/ipv4/ping_group_range
test "$(sysctl -n net.ipv4.ping_group_range | xargs)" = '0 2147483647'
sysctl net.ipv4.ping_group_range
echo 'After: IPv4 and IPv6, same ARM64 executable and unprivileged identity'
setpriv --bounding-set=-net_raw chroot --userspec=1000:1000 "$root" /usr/bin/ping -4 -n -c 3 -W 2 127.0.0.1
setpriv --bounding-set=-net_raw chroot --userspec=1000:1000 "$root" /usr/bin/ping -6 -n -c 3 -W 2 ::1
# Simulate the kernel resetting to its default on a subsequent boot.
sysctl -w net.ipv4.ping_group_range='1 0'
chroot "$root" /usr/lib/systemd/systemd-sysctl --prefix=/net/ipv4/ping_group_range
test "$(sysctl -n net.ipv4.ping_group_range | xargs)" = '0 2147483647'
setpriv --bounding-set=-net_raw chroot --userspec=1000:1000 "$root" /usr/bin/ping -4 -n -c 1 -W 2 127.0.0.1
echo 'PASS: startup sysctl ordering and repeat application restore ordinary-user ping'
TEST
