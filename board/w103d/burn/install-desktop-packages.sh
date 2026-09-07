#!/bin/bash
# Install the complete desktop contract into an offline image in private mounts.
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 MOUNTED_CLEAN_ROOT CHECKS_DIR" >&2; exit 2; }
if [[ ${W103D_PRIVATE_MOUNTS:-0} != 1 ]]; then
    exec unshare --mount env W103D_PRIVATE_MOUNTS=1 bash "$0" "$@"
fi
mount --make-rprivate /
root=$(realpath "$1"); checks=$(realpath -m "$2")
scripts=$(cd "$(dirname "$0")" && pwd)
test "$root" != /
mountpoint -q "$root"
if ! chroot "$root" /bin/true 2>/dev/null; then
    test -r /usr/lib/binfmt.d/qemu-aarch64.conf
    cat /usr/lib/binfmt.d/qemu-aarch64.conf > /proc/sys/fs/binfmt_misc/register
    chroot "$root" /bin/true
fi
test "$(chroot "$root" dpkg --print-architecture)" = arm64
mkdir -p "$checks"
test ! -e "$root/etc/resolv.conf.package-build"
test ! -e "$root/usr/sbin/policy-rc.d"
cp -a "$root/etc/resolv.conf" "$root/etc/resolv.conf.package-build"
rm "$root/etc/resolv.conf"
cp /etc/resolv.conf "$root/etc/resolv.conf"
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d"
chmod 755 "$root/usr/sbin/policy-rc.d"
disabled=()
cleanup() {
    for file in "${disabled[@]}"; do mv "$file.package-build" "$file"; done
    rm -f "$root/etc/resolv.conf" "$root/usr/sbin/policy-rc.d"
    mv "$root/etc/resolv.conf.package-build" "$root/etc/resolv.conf"
    for part in tmp run sys proc dev/pts dev; do
        mountpoint -q "$root/$part" && umount "$root/$part" || true
    done
}
trap cleanup EXIT
for file in "$root"/etc/apt/sources.list.d/armbian*.sources; do
    test -f "$file" || continue
    mv "$file" "$file.package-build"
    disabled+=("$file")
done
mount --bind /dev "$root/dev"
mount -t devpts devpts "$root/dev/pts"
mount -t proc proc "$root/proc"
mount -t sysfs -o ro sysfs "$root/sys"
mount -t tmpfs tmpfs "$root/run"
mount -t tmpfs tmpfs "$root/tmp"
mapfile -t packages < "$scripts/desktop/packages.list"
chroot "$root" apt-get -o Acquire::Retries=3 update > "$checks/apt-update.log" 2>&1
chroot "$root" apt-get -s --no-install-recommends --no-upgrade install "${packages[@]}" > "$checks/apt-plan.log" 2>&1
if grep -Eq '^Remv |^Inst (armbian-|linux-(image|dtb|u-boot|headers)|bluedevil )' "$checks/apt-plan.log"; then
    echo 'Unexpected removal or board/pairing package change; inspect apt-plan.log.' >&2
    exit 1
fi
chroot "$root" env DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends --no-upgrade --no-remove -o Acquire::Retries=3 install "${packages[@]}" > "$checks/apt-install.log" 2>&1
chroot "$root" dpkg --audit > "$checks/dpkg-audit.txt"
test ! -s "$checks/dpkg-audit.txt"
chroot "$root" apt-get -s check > "$checks/apt-check.txt" 2>&1
chroot "$root" dpkg-query -W -f='${Package}\t${Version}\t${db:Status-Abbrev}\n' > "$checks/packages.tsv"
python3 "$scripts/desktop/verify-packages.py" "$root" > "$checks/desktop-packages.json"
chroot "$root" apt-get clean
find "$root/var/lib/apt/lists" -type f -delete
find "$root/var/log" -type f -exec truncate -s 0 {} +
rm -f "$root/var/lib/systemd/random-seed" "$root/var/lib/NetworkManager/secret_key"
test ! -s "$root/etc/machine-id"
echo 'Desktop applications, optional tools and Chinese LibreOffice installed.'
