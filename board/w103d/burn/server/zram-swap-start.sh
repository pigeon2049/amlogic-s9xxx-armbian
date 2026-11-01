#!/bin/bash
# 创建 1 个 zstd 压缩、逻辑大小为物理内存 50% 的 zram swap，优先级 100
set -euo pipefail
modprobe zram 2>/dev/null || true
DEV=$(zramctl -f 2>/dev/null | head -n1)
if [[ ! "$DEV" =~ ^/dev/zram ]]; then
    [[ -w /sys/class/zram-control/hot_add ]] && cat /sys/class/zram-control/hot_add >/dev/null 2>&1 || true
    DEV=$(zramctl -f 2>/dev/null | head -n1)
fi
[[ "$DEV" =~ ^/dev/zram ]] || { echo "No free zram device"; exit 1; }
B=$(basename "$DEV")
echo zstd > "/sys/block/$B/comp_algorithm" 2>/dev/null || true
MEMKB=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
SIZE=$(( MEMKB * 1024 * 50 / 100 ))
echo "$SIZE" > "/sys/block/$B/disksize"
mkswap "$DEV" >/dev/null
swapon -p 100 "$DEV"
echo 0 > /proc/sys/vm/page-cluster
echo "zram-swap ready: $DEV size=$SIZE algo=zstd pri=100"
