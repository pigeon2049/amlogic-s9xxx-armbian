#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Check the shipping root, including identities, credentials and desktop policy."""
import argparse, configparser, ctypes, ctypes.util, json, pathlib, sys
parser=argparse.ArgumentParser()
parser.add_argument("root", type=pathlib.Path)
parser.add_argument("--before-permissions-fix", action="store_true", help="Only for checking an immutable v6/v7 input before migration")
args=parser.parse_args()
r=args.root
def read(p): return (r/p).read_text()
assert read('etc/hostname').strip()=='armbian'
if not args.before_permissions_fix:
 assert 'net.ipv4.ping_group_range = 0 2147483647' in read('etc/sysctl.d/99-w103d-ping.conf')
assert any(line in ('BOARD=w103d', 'BOARD="w103d"') for line in read('etc/armbian-release').splitlines())
preferences=read('etc/apt/preferences.d/99-w103d-board-components')
assert 'Pin-Priority: -1' in preferences
for pattern in ['armbian-bsp-*','armbian-firmware*','linux-image-*','linux-dtb-*','linux-u-boot-*','linux-headers-*']:
 assert pattern in preferences
held=set()
for block in read('var/lib/dpkg/status').split('\n\n'):
 fields=dict(line.split(': ',1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
 if fields.get('Status')=='hold ok installed':held.add(fields['Package'])
assert {'armbian-bsp-cli-odroidn2-current','linux-dtb-current-meson64','linux-u-boot-odroidn2-current','armbian-firmware'} <= held
assert not (r/'root/.not_logged_in_yet').exists()
assert read('etc/machine-id').strip()==''
assert not list((r/'etc/ssh').glob('ssh_host_*'))
assert 'ssh-keygen -A' in read('etc/systemd/system/ssh.service.d/10-w103d-hostkeys.conf')
assert 'bash /etc/custom_service/start_service.sh &' not in read('etc/rc.local')
assert 'User=armbian' in read('etc/sddm.conf.d/10-w103d.conf')
assert 'Session=plasma.desktop' in read('etc/sddm.conf.d/10-w103d.conf')
assert (r/'var/lib/w103d/desktop-ready').is_file()
assert 'LANGUAGE=zh_CN:zh:en' in read('etc/default/locale')
assert 'Name=pinyin' in read('home/armbian/.config/fcitx5/profile')
assert 'run_im none' in read('home/armbian/.xinputrc')
assert (r/'home/armbian/.config/plasma-workspace/env/input-method.sh').stat().st_mode & 0o111
assert 'S16LE' in read('etc/wireplumber/wireplumber.conf.d/51-w103d-hdmi.conf')
assert 'PlaybackPCM "hw:${CardId},0"' in read('usr/share/alsa/ucm2/W103D-HDMI/HiFi.conf')
assert 'SWAP_PRIORITY=100' in read('etc/default/armbian-zram-config')
assert 'SWAP_ALGORITHM=lz4' in read('etc/default/armbian-zram-config')
assert 'echo performance > "$p/scaling_governor"' in read('usr/local/sbin/w103d-performance')
assert (r/'usr/local/sbin/w103d-performance').stat().st_mode & 0o111
assert 'MAX_SPEED=1800000' in read('etc/default/cpufrequtils')
assert (r/'etc/systemd/system/multi-user.target.wants/w103d-performance.service').is_symlink()
assert 'ExecStart=/usr/local/sbin/w103d-performance' in read('etc/systemd/system/w103d-performance.service')
for directory in ['etc/xdg', 'etc/skel/.config', 'home/armbian/.config']:
 config=configparser.RawConfigParser();config.read(r/directory/'plasma-nm')
 assert config.getboolean('General','SystemConnectionsByDefault')
 config=configparser.RawConfigParser();config.read(r/directory/'powerdevilrc')
 for profile in ['AC', 'Battery', 'LowBattery']:
  assert not config.getboolean(profile+'][Display','DimDisplayWhenIdle')
  assert not config.getboolean(profile+'][Display','TurnOffDisplayWhenIdle')
  assert config.getint(profile+'][SuspendAndShutdown','AutoSuspendAction')==0
 config=configparser.RawConfigParser();config.read(r/directory/'kscreenlockerrc')
 assert not config.getboolean('Daemon','Autolock')
for unit in ['sleep.target', 'suspend.target', 'hibernate.target', 'hybrid-sleep.target', 'suspend-then-hibernate.target']:
 assert str((r/'etc/systemd/system'/unit).readlink())=='/dev/null'
assert 'AllowSuspend=no' in read('etc/systemd/sleep.conf.d/10-w103d-no-sleep.conf')
assert 'AllowHibernation=no' in read('etc/systemd/sleep.conf.d/10-w103d-no-sleep.conf')
assert '-s 0 -dpms' in read('etc/sddm.conf.d/20-w103d-awake.conf')
assert 'Environment=KWIN_COMPOSE=O2ES' in read('etc/systemd/user/plasma-kwin_wayland.service.d/20-w103d-gles.conf')
assert not (r/'var/lib/w103d/swapfile').exists()
for p in ['usr/share/wallpapers/W103D.png','usr/share/color-schemes/Moe.colors','usr/share/icons/Colloid/index.theme','usr/share/w103d/desktop-layout.js']:
 assert (r/p).is_file(),p
assert not [x for x in (r/'etc/NetworkManager/system-connections').glob('*') if x.is_file()]
# Debian ships these helpers here; connection configuration must be absent.
assert {x.name for x in (r/'etc/wpa_supplicant').glob('*') if x.is_file()} <= {'action_wpa.sh','functions.sh','ifupdown.sh'}
for p in ['root/.ssh','home/armbian/.ssh']:
 assert not list((r/p).glob('*')),p
assert (r/'etc/systemd/system/systemd-networkd.service').is_symlink()
assert str((r/'etc/systemd/system/systemd-networkd.service').readlink())=='/dev/null'
crypt=ctypes.CDLL(ctypes.util.find_library('crypt'))
crypt.crypt.argtypes=[ctypes.c_char_p,ctypes.c_char_p];crypt.crypt.restype=ctypes.c_char_p
shadow={line.split(':')[0]:line.split(':')[1] for line in read('etc/shadow').splitlines()}
for user in ['root','armbian']:
 assert crypt.crypt(b'1234',shadow[user].encode()).decode()==shadow[user],user
assert set(line.split(':')[0] for line in read('etc/passwd').splitlines() if 1000 <= int(line.split(':')[2]) < 65534)=={'armbian'}
print(json.dumps(dict(hostname='armbian',default_accounts=['root','armbian'],default_passwords_verified=True,first_login_skipped=True,chinese_pinyin=True,hdmi='S16LE/48000/stereo',zram='50%/lz4/priority100',swap='2GiB/priority10/created-on-board',machine_identity_clean=True,network_credentials_absent=True,automatic_dimming=False,automatic_dpms=False,automatic_lock=False,suspend_hibernate_masked=True),indent=2))
