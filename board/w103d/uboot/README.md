# W103D mainline U-Boot (chainload, production)

The box has eFuse secure-boot enabled: BL2 only accepts the vendor key,
so FIP replacement is impossible without it (proven by two black-box
tests, both rejected with `BL2 report Error, code= 19`). The production
route is chainload: the vendor BL33 runs `emmc_autoscript`, which loads
`u-boot.ext` to `0x1000000` and jumps with `go`. A missing `u-boot.ext`
falls back to vendor Linux boot. There is no brick path (maskrom +
re-flash always recovers).

## Sources

- Port source: https://github.com/pigeon2049/u-boot-zte-w103d-src
  (board code, defconfig, DTS, docs, 2 video driver patches;
  base upstream `211de43d`, `v2026.10-rc4`)
- Reference binary `u-boot-final.bin`, SHA-256
  `ea6077ff2b79d830fd4baa3e567cb1acadfca7758dfd978a74e0ac0892adbddb`
  (1,005,264 bytes), also published at
  [ophub/u-boot](https://github.com/ophub/u-boot) as
  `u-boot/amlogic/overload/u-boot-w103d.bin`
  (PR [ophub/u-boot#51](https://github.com/ophub/u-boot/pull/51))

## Key properties (all hardware-verified 2026-09-20)

- `ENV_IS_NOWHERE` (never reads eMMC env, never runs vendor bootcmd);
  self-contained bootcmd reads `uEnv.txt` (`LINUX`/`INITRD`/`FDT`/`APPEND`)
  then `booti` the same kernel/ramdisk/DTB as the stable image
- eMMC fixed at mmc dev 2 via DTS aliases (immune to SDIO probe order)
- HDMI logo: `bootup.bmp` (1280x720) centered via `bmp display`; safe
  1080p60 fallback when the sink provides no usable mode (e.g. 4K-only
  EDID beyond VENC limits); missing bmp never blocks boot
- `/w103d-video` (`ok`/`fail`) in the device-tree root for black-box
  verification: `cat /proc/device-tree/w103d-video`

## Boot contract (FAT partition, eMMC `mmc 2:1`)

- `emmc_autoscript` (compiled from `burn/emmc_autoscript.cmd`, LF-only):
  try `u-boot.ext`, else vendor Linux boot
- `uEnv.txt`: `LINUX=/zImage`, `INITRD=/ramdisk-w103d.img`,
  `FDT=/dtb-w103d/meson-g12a-w103d.dtb`, `APPEND` with
  `root=LABEL=W103D_ROOT ... console=ttyAML0,115200n8 console=tty0
  net.ifnames=0 fsck.repair=yes`
