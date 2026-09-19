echo "W103D mainline U-Boot: trying u-boot.ext"
if fatload mmc ${devnum}:1 0x1000000 u-boot.ext; then go 0x1000000; fi;
echo "W103D fallback: vendor Linux boot"
setenv kernel_addr_r 0x11000000
setenv ramdisk_addr_r 0x15000000
setenv fdt_addr_r 0x1000000
setenv bootargs 'root=LABEL=W103D_ROOT rw rootwait rootfstype=ext4 console=ttyAML0,115200n8 console=tty0 consoleblank=0 net.ifnames=0 fsck.repair=yes'
if fatload mmc ${devnum}:1 ${kernel_addr_r} zImage; then
    if fatload mmc ${devnum}:1 ${ramdisk_addr_r} ramdisk-w103d.img; then
        if fatload mmc ${devnum}:1 ${fdt_addr_r} dtb-w103d/meson-g12a-w103d.dtb; then
            fdt addr ${fdt_addr_r}
            osd close
            booti ${kernel_addr_r} ${ramdisk_addr_r} ${fdt_addr_r}
        fi
    fi
fi
echo "W103D eMMC boot returned"
