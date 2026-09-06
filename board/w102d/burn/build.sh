#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# W102D 2+16 trial, based on the clean W103D v6 pairing-fixed assembly.
set -euo pipefail
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 BASE_ASSEMBLY NEW_WORK_DIR KHADAS_TOOLS LOGO_BMP" >&2
    exit 2
fi
base=$(realpath "$1")
work=$(realpath -m "$2")
tools=$(realpath "$3")
logo=$(realpath "$4")
source=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
shared=$(realpath "$source/../../w103d/burn")
# The assembly must be new; immutable inputs are hardlinked on the same filesystem.
test ! -e "$work"
test -f "$base/checks/final-package.json"
python3 - "$base/checks/bluedevil.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r['version'] == '4:6.3.4-2+w103d1'
assert r['bluetooth_state_absent'] and not r['disconnect_import']
assert r['apt_pin_priority'] == 1001
PY
test -f "$logo"
test -x "$tools/aml_image_v2_packer_new"
mkdir -p "$work"/{payloads,bootstrap,checks}
cp "$base/checks/bluedevil.json" "$work/checks/bluedevil.json"
python3 "$source/test_bootstrap.py" --output "$work/checks/bootstrap-tests"
ln "$base/rootfs.raw" "$work/rootfs.raw"
ln "$base/bootfs.raw" "$work/bootfs.raw"
for name in DDR.USB _aml_dtb.PARTITION platform.conf dtbo.PARTITION vbmeta.PARTITION logo.PARTITION system.PARTITION data.PARTITION image.cfg; do
    ln "$base/payloads/$name" "$work/payloads/$name"
done
clang --target=arm-linux-gnueabi -march=armv7-a -marm -Os -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -static -fuse-ld=lld -Wl,--build-id=none -Wl,-e,_start "$source/bootstrap.c" -o "$work/bootstrap/init"
python3 "$shared/make_bootstrap.py" "$base/payloads/boot.PARTITION" "$work/bootstrap/init" "$work/payloads/boot.PARTITION"
cp "$work/payloads/boot.PARTITION" "$work/payloads/recovery.PARTITION"
name=W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v2.burn.img
"$tools/aml_image_v2_packer_new" -r "$work/payloads/image.cfg" "$work/payloads" "$work/$name" > "$work/checks/pack.log" 2>&1
"$tools/aml_image_v2_packer_new" -c "$work/$name" > "$work/checks/container-integrity.log" 2>&1
python3 "$shared/verify_package.py" "$work" --logo "$logo"
python3 "$source/verify_capacity_package.py" "$work" "$base"
(cd "$work" && sha256sum "$name" > "$name.sha256")
