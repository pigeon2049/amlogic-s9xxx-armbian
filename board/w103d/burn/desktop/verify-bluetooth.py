#!/usr/bin/env python3
"""Verify startup policy and the absence of captured Bluetooth identities."""
import configparser
import json
from pathlib import Path
import sys


def verify(root):
    root = Path(root)
    for relative, section, key, value in [
        ('etc/bluetooth/main.conf', 'Policy', 'AutoEnable', 'true'),
        *((directory + '/bluedevilglobalrc', 'Global', key, value)
          for directory in ('etc/xdg', 'etc/skel/.config', 'home/armbian/.config')
          for key, value in [('launchState', 'enable'), ('bluetoothBlocked', 'false')]),
    ]:
        config = configparser.RawConfigParser(delimiters=('=',))
        config.read(root / relative, encoding='utf-8')
        assert config.get(section, key) == value, (relative, key)
    link = root / 'etc/systemd/system/bluetooth.target.wants/bluetooth.service'
    assert link.is_symlink() and link.readlink().name == 'bluetooth.service'
    assert not list((root / 'var/lib/bluetooth').glob('*')), 'Shipping Bluetooth bonds/state'
    assert not list((root / 'var/lib/systemd/rfkill').glob('*:bluetooth')), 'Shipping rfkill state'
    for directory in ('etc/xdg', 'etc/skel/.config', 'home/armbian/.config'):
        config = configparser.RawConfigParser(delimiters=('=',))
        config.read(root / directory / 'bluedevilglobalrc', encoding='utf-8')
        for key in ('launchState', 'bluetoothBlocked'):
            assert not config.has_option('General', key), 'Ineffective BlueDevil 6.3.4 setting'
        assert not config.has_section('Adapters'), 'Shipping adapter identity'
        assert not config.get('Devices', 'connectedDevices', fallback='').strip(), 'Shipping device identity'
    return dict(bluez_auto_enable=True, kde_launch_state='enable', kde_config_group='Global',
                bluetooth_service_enabled=True, bluetooth_state_absent=True)


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1]), indent=2))
