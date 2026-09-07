#!/usr/bin/env python3
"""Configure BlueZ and KDE to enable Bluetooth at startup in a prepared root."""
import configparser
import os
from pathlib import Path
import subprocess
import sys


def configure(root):
    root = Path(root).resolve(strict=True)
    for relative, settings in [
        ('etc/bluetooth/main.conf', {'Policy': {'AutoEnable': 'true'}}),
        *((directory + '/bluedevilglobalrc', {'General': {
            'launchState': 'enable', 'bluetoothBlocked': 'false'}})
          for directory in ('etc/xdg', 'etc/skel/.config', 'home/armbian/.config')),
    ]:
        path = root / relative
        config = configparser.RawConfigParser(strict=False, delimiters=('=',))
        config.optionxform = str
        config.read(path, encoding='utf-8')
        for group, values in settings.items():
            if not config.has_section(group):
                config.add_section(group)
            for key, value in values.items():
                config.set(group, key, value)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Preserve ownership and paired-device/adapter entries in existing files.
        with path.open('w', encoding='utf-8') as stream:
            config.write(stream, space_around_delimiters=False)
        path.chmod(0o644)
        if relative.startswith('home/armbian/'):
            owner = (root / 'home/armbian').stat()
            os.chown(path, owner.st_uid, owner.st_gid)
    # Offline enable only: do not start/restart the host's or board's daemon.
    # This image boots systemd. Do not chroot into an ARM64 SysV helper on
    # an x86 builder merely to synchronize unused legacy runlevel links.
    subprocess.run(['systemctl', '--root=' + str(root), 'enable', 'bluetooth.service'],
                   env=dict(os.environ, SYSTEMCTL_SKIP_SYSV='1'), check=True)


if __name__ == '__main__':
    configure(sys.argv[1])
