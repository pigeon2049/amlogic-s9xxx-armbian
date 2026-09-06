# SPDX-License-Identifier: GPL-2.0-only
# KWin launches Fcitx for the native Wayland input-method protocol.
if [ "${XDG_SESSION_TYPE:-}" = wayland ]; then
    unset QT_IM_MODULE GTK_IM_MODULE
    export XMODIFIERS=@im=fcitx
fi
