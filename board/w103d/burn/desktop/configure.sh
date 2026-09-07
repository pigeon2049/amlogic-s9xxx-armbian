#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# Run inside the ARM64 target root, after installing packages.list.
set -euo pipefail
src=${W103D_DESKTOP_SOURCE:-/tmp/w103d-desktop-source}
test "$(dpkg --print-architecture)" = arm64
command -v nmtui
command -v startplasma-wayland
command -v startplasma-x11
install -D -m755 "$src/first-login.sh" /usr/local/sbin/w103d-first-login
install -d /usr/share/w103d/vendor
if ! dpkg-divert --list /etc/profile.d/armbian-check-first-login.sh | grep -q w103d; then
    dpkg-divert --local --add --rename --divert /usr/share/w103d/vendor/armbian-check-first-login.sh /etc/profile.d/armbian-check-first-login.sh
fi
install -m644 "$src/first-login-profile.sh" /etc/profile.d/armbian-check-first-login.sh
install -D -m644 "$src/ssh-hostkeys.conf" /etc/systemd/system/ssh.service.d/10-w103d-hostkeys.conf
sed -i 's/^OPENSSHD_REGENERATE_HOST_KEYS=.*/OPENSSHD_REGENERATE_HOST_KEYS=false/' /etc/default/armbian-firstrun
install -D -m644 "$src/armbian-zram-config" /etc/default/armbian-zram-config
install -D -m644 "$src/memory.conf" /etc/sysctl.d/99-w103d-desktop.conf
install -D -m644 "$src/ping.conf" /etc/sysctl.d/99-w103d-ping.conf
install -D -m755 "$src/performance.sh" /usr/local/sbin/w103d-performance
install -D -m644 "$src/performance.service" /etc/systemd/system/w103d-performance.service
install -D -m644 "$src/cpufrequtils" /etc/default/cpufrequtils
systemctl enable w103d-performance.service
install -D -m644 "$src/W103D-HDMI.conf" /usr/share/alsa/ucm2/conf.d/axg-sound-card/W103D-HDMI.conf
install -D -m644 "$src/HiFi.conf" /usr/share/alsa/ucm2/W103D-HDMI/HiFi.conf
install -D -m644 "$src/51-w103d-hdmi.conf" /etc/wireplumber/wireplumber.conf.d/51-w103d-hdmi.conf
test -s /usr/share/wallpapers/W103D.png
install -D -m755 "$src/desktop-defaults.sh" /usr/local/bin/w103d-desktop-defaults
install -d /usr/share/w103d
python3 "$src/prepare-layout.py" /usr/share/w103d/desktop-layout.js
install -D -m755 "$src/swapfile.sh" /usr/local/sbin/w103d-swapfile
install -D -m644 "$src/swapfile.service" /etc/systemd/system/w103d-swapfile.service
install -d /etc/systemd/system/sddm.service.d /etc/sddm.conf.d /var/lib/w103d
cat > /etc/systemd/system/sddm.service.d/10-first-login.conf <<'EOF'
[Unit]
ConditionPathExists=/var/lib/w103d/desktop-ready
EOF
cat > /etc/sddm.conf.d/10-w103d.conf <<'EOF'
[General]
DisplayServer=x11
InputMethod=
[Theme]
Current=breeze
[Users]
MinimumUid=1000
MaximumUid=60000
[Autologin]
User=armbian
Session=plasma.desktop
Relogin=false
EOF
cat > /etc/netplan/10-dhcp-all-interfaces.yaml <<'EOF'
network:
  version: 2
  renderer: NetworkManager
EOF
chmod 600 /etc/netplan/10-dhcp-all-interfaces.yaml
install -d /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/10-w103d.conf <<'EOF'
[main]
dns=systemd-resolved
[ifupdown]
managed=true
EOF
systemctl disable systemd-networkd.service systemd-networkd-wait-online.service NetworkManager-wait-online.service || true
systemctl mask systemd-networkd.service systemd-networkd-wait-online.service
systemctl enable NetworkManager.service systemd-resolved.service ssh.service sddm.service w103d-swapfile.service armbian-zram-config.service
systemctl disable NetworkManager-wait-online.service
systemctl set-default graphical.target
install -d /etc/skel/.config
cat > /etc/skel/.config/baloofilerc <<'EOF'
[Basic Settings]
Indexing-Enabled=false
EOF
cat > /etc/skel/.config/kwinrc <<'EOF'
[Plugins]
blurEnabled=false
backgroundcontrastEnabled=false

[Wayland]
InputMethod=/usr/share/applications/org.fcitx.Fcitx5.desktop
VirtualKeyboardEnabled=true
EOF
cat > /etc/skel/.config/plasmarc <<'EOF'
[General]
AnimationDurationFactor=0.5
EOF
# Prepare locales now. First login neither downloads locales nor geolocates.
sed -i 's/^# *\(en_US.UTF-8 UTF-8\)/\1/;s/^# *\(zh_CN.UTF-8 UTF-8\)/\1/' /etc/locale.gen
locale-gen
update-locale --reset LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh:en
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
echo Asia/Shanghai > /etc/timezone
echo armbian > /etc/hostname
sed -i 's/^127\.0\.1\.1.*/127.0.1.1 armbian/' /etc/hosts
# Desktop pressure protection, with no special preference for killing apps.
cat > /etc/default/earlyoom <<'EOF'
EARLYOOM_ARGS="-r 0 -m 5 -s 10"
EOF
systemctl enable earlyoom.service
install -d /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/10-w103d.conf <<'EOF'
[Journal]
SystemMaxUse=64M
RuntimeMaxUse=32M
EOF
install -d /etc/default
cat > /etc/default/armbian-ramlog <<'EOF'
ENABLED=true
SIZE=50M
USE_RSYNC=true
EOF
if ! id armbian >/dev/null 2>&1; then useradd -m -U -s /bin/bash armbian; fi
test "$(id -u armbian)" -ge 1000
for group in sudo audio video render input netdev plugdev bluetooth; do
    if getent group "$group" >/dev/null; then usermod -aG "$group" armbian; fi
done
# The user explicitly requested these default credentials and no setup wizard.
printf 'root:1234\narmbian:1234\n' | chpasswd
install -m644 -o armbian -g armbian "$src/xinputrc" /home/armbian/.xinputrc
install -d -o armbian -g armbian /home/armbian/.config/fcitx5 /home/armbian/.config/autostart
install -d -o armbian -g armbian /home/armbian/.config/plasma-workspace/env
install -m755 "$src/input-method.sh" /home/armbian/.config/plasma-workspace/env/input-method.sh
cat > /home/armbian/.config/plasma-localerc <<'EOF'
[Formats]
LANG=zh_CN.UTF-8
[Translations]
LANGUAGE=zh_CN:zh:en
EOF
install -m644 "$src/fcitx5-profile" /home/armbian/.config/fcitx5/profile
cat > /home/armbian/.config/autostart/w103d-desktop.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=W103D desktop defaults
Exec=/usr/local/bin/w103d-desktop-defaults
OnlyShowIn=KDE;
X-KDE-autostart-phase=2
EOF
cp /etc/skel/.config/{baloofilerc,kwinrc,plasmarc} /home/armbian/.config/
chown -R armbian:armbian /home/armbian/.config
python3 "$src/configure-power.py" /
python3 "$src/configure-bluetooth.py" /
python3 "$src/disable-legacy-startup.py" /
install -D -m644 "$src/kwin-gles.conf" /etc/systemd/user/plasma-kwin_wayland.service.d/20-w103d-gles.conf
install -D -m644 "$src/plasma-nm" /etc/xdg/plasma-nm
install -D -m644 "$src/plasma-nm" /etc/skel/.config/plasma-nm
install -m644 -o armbian -g armbian "$src/plasma-nm" /home/armbian/.config/plasma-nm
touch /var/lib/w103d/desktop-ready /var/lib/w103d/root-password-set
python3 "$src/protect-upgrades.py" /
rm -f /root/.not_logged_in_yet
for p in /etc/systemd/system/getty@.service.d/override.conf /etc/systemd/system/getty@tty1.service.d/override.conf /etc/systemd/system/serial-getty@.service.d/override.conf; do
    if test -f "$p" && grep -q -- '--autologin root' "$p"; then rm "$p"; fi
done
echo 'KDE, automatic desktop login, NetworkManager, SSH host-key recovery and memory policy configured.'
