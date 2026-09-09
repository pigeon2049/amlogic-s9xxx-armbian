#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Compatibility filename for the same universal image; no model-specific payload.
set -euo pipefail
[[ $# == 4 ]] || { echo "Usage: $0 BASE_ASSEMBLY NEW_WORK_DIR TOOLS LOGO_BMP" >&2; exit 2; }
shared=$(cd "$(dirname "$0")/../../w103d/burn" && pwd)
exec bash "$shared/rebuild-bootstrap.sh" "$@" W102D_Armbian_26.8.1_6.18.49_KDE_16GB_TEST_v4.burn.img
