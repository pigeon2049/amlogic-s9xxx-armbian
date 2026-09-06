# BlueDevil 6.3.4 pairing backport

Backport KDE commit `dff9c79ca81370ed72f672b45ac39ec3d1c09875`, which
removes the unconditional disconnect after pairing. It reverts workaround
`27c8634b88014d2e10a3f316d43d307f5085a3dc`.

Upstream: https://invent.kde.org/plasma/bluedevil/-/commit/dff9c79ca81370ed72f672b45ac39ec3d1c09875

On the tested Designer Compact Keyboard, the old wizard issued Device1.Disconnect
immediately after pairing and subsequent encryption failed with PIN or Key Missing.
The kernel, BlueZ security policy, Bluetooth firmware and battery handling are not
part of this fix.

`CMakeLists.txt` builds only the original wizard sources, with the same Qt/KF minimum
versions as BlueDevil 6.3.4. Apply `no-disconnect.patch` to the upstream v6.3.4 source,
then build inside a Debian trixie arm64 build environment:

```sh
cmake -S . -B build -G Ninja \
  -DBLUEDEVIL_SOURCE=/absolute/path/to/patched/bluedevil \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build build --target bluedevil-wizard --parallel 2
```

The patched Debian package is made from the original `4:6.3.4-2` arm64 package,
retaining its other binaries, translations and maintainer scripts. The local
revision is `4:6.3.4-2+w103d1`; deployment and rollback are recorded in the project
diagnostic document. `package_backport.py ORIGINAL.deb build/bin/bluedevil-wizard OUTPUT`
checks that only the wizard payload changed. Build and repack on a Linux filesystem
to retain Unix permissions. `package-check.json` records the exact board-tested
artifact; the image installer rejects other bytes, including unvalidated rebuilds.

## Cause and validation

The wizard's immediate disconnect interrupted the new encrypted HID connection.
The tested keyboard subsequently rejected encryption with `PIN or Key Missing`.
Clearing inconsistent bonds and pairing through BlueZ worked; after applying the
upstream revert, pairing through the KDE GUI also completed and the user confirmed
normal typing. The GUI D-Bus trace contained Pair and Connect, with no Disconnect;
HCI reported successful AES-CCM encryption. This is a desktop pairing regression,
not evidence of a Bluetooth kernel-driver fault. Raw traces and pairing keys are
kept out of this repository.

## W103D v6 and W102D v2 images

Start from the clean, verified W103D v5 assembly, not the compiler chroot or a
filesystem copied from the running board. Use native ARM64 or QEMU aarch64 binfmt:

```sh
bash board/w103d/burn/prepare-pairing-root.sh \
  /work/w103d-v5/rootfs.raw /work/kde-v6 /artifacts/bluedevil_6.3.4-2+w103d1_arm64.deb
bash board/w103d/burn/assemble-desktop.sh \
  /work/w103d-v5 /work/kde-v6/rootfs.raw /work/w103d-v6 /work/khadas-tools
python3 board/w103d/burn/verify_package.py /work/w103d-v6 --logo /work/bootup.bmp
python3 board/w103d/burn/verify-desktop-boot.py /work/w103d-v6 \
  --kernel /work/Image-6.18.49-ophub --initrd /work/initrd.img-6.18.49-ophub
```

The installer runs dpkg with service starts disabled, installs `pairing.pref`,
and restores any existing service policy. The preparation checks both first and
repeat installation. Packaging requires the tested wizard hash, package version,
removed disconnect import, APT pin, and an empty Bluetooth state directory.
Existing desktop and board-component protection checks also remain mandatory.
No kernel, module, BlueZ policy, firmware or battery behavior is changed.

On `w102d-burn-6.18`, use `board/w102d/burn/build.sh` with the verified W103D v6
assembly to produce the 16 GB v2 trial. Its root and boot filesystems are identical
to W103D v6; only the existing capacity-specific provisioning differs.

The local binary package and new USB Burning images are release artifacts, not
Git payloads. A new rebuild must be validated before updating the hash manifest.
To roll back the application, remove `/etc/apt/preferences.d/w103d-bluedevil-pairing`
and install the original `4:6.3.4-2` Debian package. Remove the same pin when adopting
a tested official package that contains the upstream fix.
