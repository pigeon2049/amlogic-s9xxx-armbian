#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Install W103D package protection in a prepared root, without running its code."""
import fnmatch
import pathlib
import subprocess
import sys

PATTERNS = ('armbian-bsp-*', 'armbian-firmware*', 'linux-image-*',
            'linux-dtb-*', 'linux-u-boot-*', 'linux-headers-*')


def main():
    root = pathlib.Path(sys.argv[1]).resolve(strict=True)
    release = (root / 'etc/armbian-release').read_text()
    if not any(line in ('BOARD=w103d', 'BOARD="w103d"') for line in release.splitlines()):
        raise SystemExit('Expected a prepared W103D root; refusing another board.')
    if not (root / 'usr/lib/modules/6.18.49-ophub').is_dir():
        raise SystemExit('Expected the matched 6.18.49-ophub module tree.')
    source = pathlib.Path(__file__).with_name('upgrade-protection.pref')
    target = root / 'etc/apt/preferences.d/99-w103d-board-components'
    preference = source.read_bytes().replace(b'\r\n', b'\n')
    held = []
    for block in (root / 'var/lib/dpkg/status').read_text().split('\n\n'):
        fields = dict(line.split(': ', 1) for line in block.splitlines()
                      if ': ' in line and not line.startswith(' '))
        name = fields.get('Package', '')
        if fields.get('Status', '').endswith(' ok installed') and any(
                fnmatch.fnmatchcase(name, pattern) for pattern in PATTERNS):
            held.append(name)
    required = {'armbian-bsp-cli-odroidn2-current', 'linux-dtb-current-meson64',
                'linux-u-boot-odroidn2-current', 'armbian-firmware'}
    if not required <= set(held):
        raise SystemExit('Expected the validated base package registrations.')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(preference)
    target.chmod(0o644)
    subprocess.run(['dpkg', '--admindir=' + str(root / 'var/lib/dpkg'),
                    '--set-selections'], input=''.join(name + ' hold\n' for name in held),
                   text=True, check=True)
    print('Protected W103D board packages: ' + ', '.join(sorted(held)))


if __name__ == '__main__':
    main()
