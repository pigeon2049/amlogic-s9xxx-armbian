echo "W103D Linux 6.18 eMMC boot"
setenv kernel_addr_r 0x11000000
setenv ramdisk_addr_r 0x15000000
setenv fdt_addr_r 0x1000000
setenv bootargs 'root=LABEL=W103D_ROOT rw rootwait rootfstype=ext4 console=ttyAML0,115200n8 console=tty0 consoleblank=0 net.ifnames=0 fsck.repair=yes'
if fatload mmc ${devnum}:1 ${kernel_addr_r} zImage; then
    if fatload mmc ${devnum}:1 ${ramdisk_addr_r} uInitrd; then
        if fatload mmc ${devnum}:1 ${fdt_addr_r} dtb/amlogic/meson-g12a-w103d.dtb; then
            fdt addr ${fdt_addr_r}
            osd close
            booti ${kernel_addr_r} ${ramdisk_addr_r} ${fdt_addr_r}
        fi
    fi
fi
echo "W103D eMMC boot returned"
