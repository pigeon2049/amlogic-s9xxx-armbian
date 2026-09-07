# KDE v7: Bluetooth startup and both wireless fixes

**Historical recipe:** v7/v3 wrote the wrong KDE group. Use [v8-README.md](v8-README.md) for the corrected release.

Generated artifacts and verification boundaries: [v7-validation.md](v7-validation.md).

The v7 recipe enables `bluetooth.service`, explicitly sets BlueZ
`[Policy] AutoEnable=true`, and sets KDE BlueDevil `[General] launchState=enable`
and `bluetoothBlocked=false` for the default user and future users.
BlueDevil 6.3.4 otherwise defaults to remembering the previous state: the
diagnosed board had an adapter's `powered=false` saved in `bluedevilglobalrc`
despite an enabled daemon. Its startup code restores that setting and can
turn the controller off after BlueZ starts it.

This uses KDE's existing “enable Bluetooth at login” setting. It unblocks
Bluetooth and powers adapters when the BlueZ manager becomes operational;
there is no fixed-delay polling loop. Users may still turn Bluetooth off
during a session or change their startup preference. Existing pairing keys
are preserved by the configuration helper. Shipping-image checks reject
captured bonds, adapter identities and saved Bluetooth rfkill state. A clean
flash still requires pairing the mouse once; the image does not contain the
developer's mouse keys.

Source references: [BlueDevil settings](https://invent.kde.org/plasma/bluedevil/-/blob/v6.3.4/src/kcm/bluetooth.cpp),
[startup handling](https://invent.kde.org/plasma/bluedevil/-/blob/v6.3.4/src/kded/devicemonitor.cpp),
[BlueZ policy](https://github.com/bluez/bluez/blob/5.82/src/main.conf).

## Build from the clean v6 root

```sh
bash board/w103d/burn/prepare-wireless-root.sh \
  /work/w103d-v6/rootfs.raw /work/kde-v7 \
  /work/connection-rate-final.ko /work/mac80211-data-rate.ko
bash board/w103d/burn/assemble-desktop.sh \
  /work/w103d-v6 /work/kde-v7/rootfs.raw /work/w103d-v7 /work/khadas-tools
python3 board/w103d/burn/verify_package.py /work/w103d-v7 --logo /work/bootup.bmp
```

Both `mt7663s.ko` and `mac80211.ko` are required. `wireless-modules.json` pins
the exact 2026-09-07 board-tested pair, including the scan connection-probe
and payload TX reporting fixes. Installation preflights both artifacts;
packaging independently checks hashes of decompressed modules, complete
`6.18.49-ophub` vermagic, dependencies and SDIO alias. Merely supplying an older
module with the same kernel release fails. The initramfs must contain neither
module, so an embedded older copy cannot override the root filesystem.
Rebuilds require explicit `LOCALVERSION=-ophub` and a newly validated manifest;
never change vermagic to bypass ABI checks.

The BlueDevil pairing backport and APT protection remain required. The local
board's 5 GHz-only SSID preference is not shipped. Scanning packet loss is
still unresolved; see [wireless validation](../linux/scan-rate-validation.md).

The W102D branch's v3 recipe must consume this verified v7 assembly, check
its mounted root and boot image again, and carry the same two module hashes
and Bluetooth policy. Its 16 GB bootstrap remains a capacity trial; W103D
validation does not establish W102D hardware compatibility.
