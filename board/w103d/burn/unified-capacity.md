# Unified W103D / W102D capacity-adaptive USB image

2026-09-10. Both models now use one bootstrap implementation and identical
firmware bytes. Existing W103D v8 / W102D v4 names are compatibility entry
points, not different capacity builds. No version number is incremented.

## Reason

A W103D running the known-good Android image reports eMMC Y2P032 with
61,071,360 sectors. The old W103D bootstrap accepted exactly 60,620,800 and
stopped before installing the Armbian boot entry. Its EPT validation and MBR
length were also fixed to that one device. The W102D fork accepted only a
nominal 16 GB range. Neither restriction is necessary when the image fits.

Android DTB comparison showed only bootargs differences against the saved
factory runtime tree. The project LED GPIO configuration remains authoritative;
no Android DTB/LED configuration is imported by this fix.

## Capacity contract

The shared bootstrap reads actual 512-byte sectors from sysfs, verifies eMMC
boot0 exists, validates the fixed EPT offsets and checks that EPT data spans
the actual remaining capacity. It reads the ext4 block count and block size
and rejects a root filesystem that cannot fit, including 64-bit block-count
and arithmetic overflow cases. It computes the MBR root length from measured
capacity and retains the original environment CRC and write/readback checks.
No model, eMMC vendor, or nominal capacity whitelist remains.

The existing MBR implementation represents at most 4,294,967,295 sectors.
Larger capacities and malformed/overflowing decimal input are rejected.
This is an on-disk format/arithmetic bound, not a 16/32 GB model restriction.
The current 8 GiB rootfs requires at least 20,779,008 sectors in total,
including the 1954 MiB front reservation (10,638,852,096 bytes).
The package verifier checks raw root length equals its ext4 declared extent,
so this runtime fit condition covers the complete sparse payload.

Internal filesystem labels and environment keys retain the W103D names.
W102D legacy source/build/test entries delegate to the shared implementation.
DDR/U-Boot, both DTBs, LED GPIO, kernel/modules, rootfs, FAT and desktop are
retained. Only boot/recovery initialization payloads and their VERIFY records
change relative to the previous W103D package. The normal desktop builder
also recompiles current bootstrap source instead of copying a stale init.

## Build

Run from an exact Git source archive on Linux with root/loop privileges:

```sh
python3 board/w103d/burn/test_bootstrap.py --output /work/capacity-tests
bash board/w103d/burn/rebuild-bootstrap.sh \
  /work/verified-v8 /work/unified-v8 /work/khadas-tools /work/bootup.bmp
```

The input assembly must include the existing clean desktop raw files, payloads
and verification reports. The new directory must not exist and must be on the
same filesystem: immutable filesystem/payload inputs are hardlinked. Actual
root/boot components, ABI, signatures and script LF/CRC are rechecked. The
builder packs the new init, verifies payloads/sparse data, and compares all
unchanged payloads. W102D's old build entry invokes the same builder using
its legacy v4 filename; the resulting container bytes are identical.

The regression suite runs actual ARM provisioning code under qemu-user,
including the reported 61,071,360-sector case, larger capacities, exact fit,
one-sector-short capacity, 1/2/4/64 KiB blocks, malformed/overflowing input,
corrupt EPT/filesystems/environment, readback and repeat execution. Rejection
cases verify the inspected storage regions remain byte-identical. This does
not emulate hardware discovery, U-Boot, or a physical flash/boot test.

Current artifacts and SHA-256 are recorded separately after the build.
The previous Android read-only diagnosis establishes the capacity mismatch;
booting the repaired universal image on each physical model remains required.
