#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Apply the requested always-awake policy to a live or offline W103D root."""
import configparser
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/')

def ini(path, groups):
    target = root / path
    config = configparser.RawConfigParser(strict=False, delimiters=('=',), interpolation=None)
    config.optionxform = str
    if target.exists():
        config.read(target, encoding='utf-8')
    for group, values in groups.items():
        if not config.has_section(group):
            config.add_section(group)
        for key, value in values.items():
            config.set(group, key, str(value))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8') as stream:
        config.write(stream, space_around_delimiters=False)
    target.chmod(0o644)

power = {'BatteryManagement': {'BatteryCriticalAction': 0}}
for profile in ('AC', 'Battery', 'LowBattery'):
    power[f'{profile}][Display'] = {
        'DimDisplayWhenIdle': 'false',
        'TurnOffDisplayWhenIdle': 'false',
        'TurnOffDisplayIdleTimeoutSec': -1,
        'TurnOffDisplayIdleTimeoutWhenLockedSec': -1,
        'LockBeforeTurnOffDisplay': 'false',
        'UseProfileSpecificDisplayBrightness': 'false',
    }
    power[f'{profile}][SuspendAndShutdown'] = {
        'AutoSuspendAction': 0, 'PowerButtonAction': 0, 'PowerDownAction': 0, 'LidAction': 0,
    }
locker = {'Daemon': {'Autolock': 'false', 'LockOnResume': 'false', 'LockOnStart': 'false'}}
for directory in ('etc/xdg', 'etc/skel/.config', 'home/armbian/.config'):
    ini(directory + '/powerdevilrc', power)
    ini(directory + '/kscreenlockerrc', locker)
    # Do not allow an old Plasma 5 profile to replace the new Plasma 6 policy.
    ini(directory + '/powermanagementprofilesrc', {'Migration': {'MigratedProfilesToPlasma6': 'powerdevilrc'}})

ini('etc/systemd/sleep.conf.d/10-w103d-no-sleep.conf', {'Sleep': {
    'AllowSuspend': 'no', 'AllowHibernation': 'no',
    'AllowHybridSleep': 'no', 'AllowSuspendThenHibernate': 'no',
}})
ini('etc/systemd/logind.conf.d/10-w103d-no-idle.conf', {'Login': {
    'IdleAction': 'ignore', 'HandleSuspendKey': 'ignore', 'HandleSuspendKeyLongPress': 'ignore',
    'HandleHibernateKey': 'ignore', 'HandleHibernateKeyLongPress': 'ignore',
    'HandleLidSwitch': 'ignore', 'HandleLidSwitchExternalPower': 'ignore', 'HandleLidSwitchDocked': 'ignore',
}})
for name in ('sleep.target', 'suspend.target', 'hibernate.target', 'hybrid-sleep.target',
             'suspend-then-hibernate.target', 'systemd-suspend.service', 'systemd-hibernate.service',
             'systemd-hybrid-sleep.service', 'systemd-suspend-then-hibernate.service'):
    target = root / 'etc/systemd/system' / name
    if target.is_symlink() and str(target.readlink()) == '/dev/null':
        continue
    if target.exists() or target.is_symlink():
        raise RuntimeError(f'Refusing to replace an existing local unit: {target}')
    target.symlink_to('/dev/null')

# X11 greeter and optional X11 desktop have their own screen saver / DPMS timers.
ini('etc/sddm.conf.d/20-w103d-awake.conf', {'X11': {'ServerArguments': '-nolisten tcp -s 0 -dpms'}})
script = root / 'usr/local/bin/w103d-x11-awake'
script.parent.mkdir(parents=True, exist_ok=True)
script.write_text('#!/bin/sh\nif [ "${XDG_SESSION_TYPE:-}" = x11 ] && command -v xset >/dev/null 2>&1; then\n    xset s off\n    xset -dpms\nfi\n')
script.chmod(0o755)
ini('etc/xdg/autostart/w103d-x11-awake.desktop', {'Desktop Entry': {
    'Type': 'Application', 'Name': 'W103D keep X11 awake', 'Exec': '/usr/local/bin/w103d-x11-awake',
    'OnlyShowIn': 'KDE;', 'X-KDE-autostart-phase': 2,
}})
ini('etc/NetworkManager/conf.d/20-w103d-no-wifi-powersave.conf', {'connection': {'wifi.powersave': 2}})

# These files are also written to a clean image before its first desktop login.
for line in (root / 'etc/passwd').read_text().splitlines():
    fields = line.split(':')
    if fields[0] == 'armbian':
        for name in ('powerdevilrc', 'kscreenlockerrc', 'powermanagementprofilesrc'):
            os.chown(root / 'home/armbian/.config' / name, int(fields[2]), int(fields[3]))
        break
print('Automatic dimming, DPMS, locking, suspend and hibernation disabled; Wi-Fi power-save default disabled.')
