# BlueDevil 6.3.4 startup and ordinary-user ping

Date: 2026-09-07. Source changes apply to both W103D and W102D desktop roots.

The v7/v3 configurator incorrectly wrote `launchState` and `bluetoothBlocked`
in `[General]`. The shipped `4:6.3.4-2+w103d1` daemon and settings page read
`[Global]`: checked against upstream tag v6.3.4, `src/kded/devicemonitor.cpp`
and `src/kcm/bluetooth.cpp`. Therefore the old tests accepted a setting the
application ignored. Configure the correct group and remove only the two
ineffective keys from General, retaining other preferences and pairing data.

Fresh configuration and incremental updates also install
`/etc/sysctl.d/99-w103d-ping.conf` with `net.ipv4.ping_group_range = 0 2147483647`.
The original image has neither ping file capabilities/setuid nor an allowed
Echo socket group range. The new policy permits ordinary-user Echo sockets
without granting raw-socket capabilities to ping.

Validation used an independent copy of the actual clean v7 ARM64 root:

- Four Bluetooth regressions pass, including rejection of the original
  General-only configuration and migration from a saved Global/disable.
- Actual ARM64 kreadconfig6 returns Global/launchState=enable for all three
  config locations. The original root fails the corrected Bluetooth check.
- Complete desktop-root checks and corrected Bluetooth shipping checks pass.
- In an isolated Linux network/mount namespace, QEMU executes the image's
  actual ping as uid/gid 1000, with NET_RAW removed from the bounding set.
  The kernel default `1 0` reproduces the reported capability/setuid error
  (exit 2). Applying the image's actual systemd-sysctl, restricted to this
  key but using normal file precedence, yields `0 2147483647`.
  IPv4 and IPv6 loopback each pass 3/3. Resetting the parameter and repeating
  startup application restores permission and passes a further IPv4 ping.

This uses the WSL kernel and QEMU user-mode execution; it is not a guest
kernel boot, board reboot, gateway performance test or Bluetooth hardware
test. Evidence: workspace `output/research/20260907-ping-bluetooth/`.
The board could not be reached over SSH. No board state, kernel/module,
firmware, or original v7/v3 container was changed. No new burn container
has been assembled. Bluetooth mouse reconnection remains unverified.
