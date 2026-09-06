#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Local/SSH account setup. No external requests or package installation.
set -euo pipefail
export LC_ALL=C.UTF-8
marker=/root/.not_logged_in_yet
[[ $EUID == 0 && -f "$marker" && -t 0 ]] || exit 0
install -d -m700 /var/lib/w103d
exec 9>/run/w103d-first-login.lock
flock -n 9 || { echo 'Setup is already running in another terminal.'; exit 1; }
for p in /etc/systemd/system/getty@.service.d/override.conf \
         /etc/systemd/system/getty@tty1.service.d/override.conf \
         /etc/systemd/system/serial-getty@.service.d/override.conf; do
    if [[ -f "$p" ]] && grep -q -- '--autologin root' "$p"; then rm "$p"; fi
done
systemctl daemon-reload
echo
echo 'W103D KDE first setup (Internet is optional)'
if [[ ! -e /var/lib/w103d/network-setup-seen ]]; then
    echo 'You can connect Wi-Fi now with nmtui, or later from the KDE network icon.'
    read -r -p 'Open Wi-Fi/network setup now? [Y/n] ' choice
    if [[ ! "$choice" =~ ^[Nn]$ ]]; then
        systemctl start NetworkManager
        nmcli radio wifi on || true
        nmtui || echo 'Network setup closed. Continuing offline.'
    fi
    touch /var/lib/w103d/network-setup-seen
    sync -f /var/lib/w103d
fi
if [[ ! -e /var/lib/w103d/root-password-set ]]; then
    echo 'Set the root administrator password.'
    until passwd root; do echo 'Password was not changed; please retry.'; done
    sync -f /etc/shadow
    touch /var/lib/w103d/root-password-set
    sync -f /var/lib/w103d
fi
state=/var/lib/w103d/first-login-user
if [[ -s "$state" ]]; then
    read -r username < "$state"
else
    while :; do
        read -r -p 'New desktop username [armbian]: ' username
        username=${username:-armbian}
        if [[ "$username" =~ ^[a-z][a-z0-9_-]{0,30}$ ]] && ! getent passwd "$username" >/dev/null; then break; fi
        echo 'Choose a new name starting with a lowercase letter (maximum 31 characters).'
    done
    printf '%s\n' "$username" > "$state"
    chmod 600 "$state"
fi
[[ "$username" =~ ^[a-z][a-z0-9_-]{0,30}$ ]] || { echo 'Invalid setup state.'; exit 1; }
if ! getent passwd "$username" >/dev/null; then
    useradd --create-home --user-group --shell /bin/bash "$username"
fi
[[ $(id -u "$username") -ge 1000 ]] || { echo 'Refusing a system account.'; exit 1; }
for group in sudo audio video render input netdev plugdev bluetooth; do
    if getent group "$group" >/dev/null; then usermod -aG "$group" "$username"; fi
done
echo "Set the desktop password for $username."
until passwd "$username"; do echo 'Password was not changed; please retry.'; done
# Complete the account before allowing SDDM to start. Restarting this setup
# after power loss resumes the same account and keeps the marker until done.
runuser -u "$username" -- im-config -n fcitx5
touch /var/lib/w103d/desktop-ready
rm "$marker"
sync
echo 'Setup complete. Starting KDE login. Select your desktop user and enter its password.'
echo 'Wi-Fi: KDE network icon, or nmtui in a terminal. No Internet is required to log in.'
systemctl reset-failed sddm.service || true
systemctl start --no-block sddm.service
