#!/bin/bash
# Give a freshly flashed box a unique name from its Wi-Fi MAC: armbian -> w103d-xxxx.
set -euo pipefail
marker=/var/lib/w103d/hostname-done
[[ $(hostname) == armbian ]] || { install -D /dev/null "$marker"; exit 0; }
mac=$(cat /sys/class/net/wlan0/address)
name="w103d-$(echo "$mac" | tr -d ':' | tail -c 5)"
hostnamectl set-hostname "$name"
sed -i "s/^127\.0\.1\.1\s.*/127.0.1.1   $name/" /etc/hosts
install -D /dev/null "$marker"
echo "hostname set to $name"
