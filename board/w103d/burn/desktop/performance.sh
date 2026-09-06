#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Use the existing W103D OPP; thermal cooling can still limit the CPU.
set -eu
p=/sys/devices/system/cpu/cpufreq/policy0
test "$(cat "$p/cpuinfo_max_freq")" = 1800000
echo performance > "$p/scaling_governor"
