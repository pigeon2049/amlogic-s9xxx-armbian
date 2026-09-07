#!/bin/bash
# Smoke-test shipped ARM64 binaries without storing a test profile in the image.
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 MOUNTED_ROOT CHECKS_DIR" >&2; exit 2; }
if [[ ${W103D_APP_PRIVATE_MOUNTS:-0} != 1 ]]; then
    exec unshare --mount env W103D_APP_PRIVATE_MOUNTS=1 bash "$0" "$@"
fi
mount --make-rprivate /
root=$(realpath "$1"); checks=$(realpath -m "$2")
test "$root" != /
mountpoint -q "$root"
mkdir -p "$checks"
mount --bind /dev "$root/dev"
mount -t proc proc "$root/proc"
mount -t tmpfs tmpfs "$root/tmp"
trap 'umount "$root/tmp" "$root/proc" "$root/dev"' EXIT
mkdir -p "$root/tmp/office-test"
chmod 777 "$root/tmp/office-test"
mkdir "$root/tmp/office-test/runtime"
chmod 700 "$root/tmp/office-test/runtime"
chown --reference="$root/home/armbian" "$root/tmp/office-test/runtime"
unset DISPLAY WAYLAND_DISPLAY DBUS_SESSION_BUS_ADDRESS
export XDG_RUNTIME_DIR=/tmp/office-test/runtime
export XDG_CONFIG_HOME=/tmp/office-test/config
export XDG_CACHE_HOME=/tmp/office-test/cache
cat > "$root/tmp/office-test/chinese.html" <<'HTML'
<!doctype html><html lang="zh-CN"><meta charset="utf-8"><body>
<h1>中文办公测试</h1><p>LibreOffice 简体中文文档导出正常。</p>
<table><tr><td>项目</td><td>数量</td></tr><tr><td>桌面软件</td><td>123</td></tr></table>
</body></html>
HTML
chroot "$root" runuser -u armbian -- env HOME=/tmp/office-test LC_ALL=zh_CN.UTF-8 XDG_CACHE_HOME=/tmp/office-test/cache SAL_USE_VCLPLUGIN=svp \
    timeout 240 libreoffice -env:UserInstallation=file:///tmp/office-test/profile --headless --convert-to pdf --outdir /tmp/office-test /tmp/office-test/chinese.html > "$checks/libreoffice-convert.log" 2>&1
test -s "$root/tmp/office-test/chinese.pdf"
cp "$root/tmp/office-test/chinese.pdf" "$checks/libreoffice-chinese.pdf"
pdftotext "$checks/libreoffice-chinese.pdf" "$checks/libreoffice-chinese.txt"
grep -q '中文办公测试' "$checks/libreoffice-chinese.txt"
grep -q '123' "$checks/libreoffice-chinese.txt"
chroot "$root" runuser -u armbian -- env HOME=/tmp/office-test bash -c '
    set -e
    xdg-open --version
    notify-send --version
    libreoffice --headless --version
    java -version
    ffmpeg -version > /tmp/office-test/ffmpeg.txt
    mpv --version > /tmp/office-test/mpv.txt
    vlc --version > /tmp/office-test/vlc.txt
    7z > /tmp/office-test/7zip.txt
    head -n 1 /tmp/office-test/{ffmpeg,mpv,vlc}.txt
    head -n 3 /tmp/office-test/7zip.txt
' > "$checks/application-versions.txt" 2>&1
chroot "$root" runuser -u armbian -- env HOME=/tmp/office-test VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.json \
    timeout 120 vulkaninfo --summary > "$checks/vulkan-software.txt" 2>&1
grep -q 'PHYSICAL_DEVICE_TYPE_CPU' "$checks/vulkan-software.txt"
printf '%s\n' '{"arm64_binaries":true,"ordinary_user":true,"libreoffice_chinese_pdf":true,"vulkan_software_enumerated":true,"vulkan_hardware_tested":false}' > "$checks/applications-runtime.json"
echo 'ARM64 application startup, Chinese PDF export and software Vulkan passed.'
