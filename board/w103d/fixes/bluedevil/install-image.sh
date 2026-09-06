#!/bin/bash
# Install only into an offline mounted image. Requires native ARM64 or QEMU binfmt.
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 MOUNTED_CLEAN_ROOT TESTED_BACKPORT.deb" >&2; exit 2; }
root=$(realpath "$1"); deb=$(realpath "$2")
source=$(cd "$(dirname "$0")" && pwd)
test "$root" != /
mountpoint -q "$root"
test -d "$root/usr/lib/modules/6.18.49-ophub"
grep -Eq '^BOARD="?w103d"?$' "$root/etc/armbian-release"
expected=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["package_sha256"])' "$source/package-check.json")
echo "$expected  $deb" | sha256sum -c -
test "$(dpkg-deb -f "$deb" Package)" = bluedevil
test "$(dpkg-deb -f "$deb" Version)" = '4:6.3.4-2+w103d1'
test "$(dpkg-deb -f "$deb" Architecture)" = arm64
version=$(chroot "$root" dpkg-query -W '-f=${Version}' bluedevil)
[[ "$version" == '4:6.3.4-2' || "$version" == '4:6.3.4-2+w103d1' ]]
stage=$(mktemp -d "$root/tmp/bluedevil-image.XXXXXX")
policy="$root/usr/sbin/policy-rc.d"
had_policy=0
if test -e "$policy" || test -L "$policy"; then
    cp -a "$policy" "$stage/policy-rc.d"
    had_policy=1
fi
cleanup() {
    rm -f "$policy"
    if test "$had_policy" = 1; then cp -a "$stage/policy-rc.d" "$policy"; fi
    rm -f "$stage/policy-rc.d" "$stage/backport.deb"
    rmdir "$stage"
}
trap cleanup EXIT
# Replace rather than follow a possible policy symlink; restore it in the trap.
rm -f "$policy"
printf '#!/bin/sh\nexit 101\n' > "$policy"
chmod 755 "$policy"
install -m644 "$deb" "$stage/backport.deb"
chroot "$root" dpkg --simulate --install "${stage#"$root"}/backport.deb"
chroot "$root" dpkg --install "${stage#"$root"}/backport.deb"
install -D -m644 "$source/pairing.pref" "$root/etc/apt/preferences.d/w103d-bluedevil-pairing"
audit=$(chroot "$root" dpkg --audit)
test -z "$audit" || { echo "$audit" >&2; exit 1; }
python3 "$source/verify-root.py" "$root"
