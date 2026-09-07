#!/usr/bin/env python3
"""Verify the explicit desktop package contract in an offline ARM64 root."""
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
installed = {}
providers = {}
for block in (root / 'var/lib/dpkg/status').read_text().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines()
                  if ': ' in line and not line.startswith((' ', '\t')))
    if not fields.get('Status', '').endswith(' ok installed'):
        continue
    name = fields['Package']
    installed[name] = fields['Version']
    for item in fields.get('Provides', '').split(','):
        alias = re.split(r'\s|\(', item.strip())[0]
        if alias:
            providers[alias] = name
required = pathlib.Path(__file__).with_name('packages.list').read_text().split()
missing = sorted(set(required) - installed.keys() - providers.keys())
assert not missing, f'Missing desktop packages: {missing}'
for command in ['xdg-open', 'notify-send', 'vulkaninfo', 'libreoffice', 'ffmpeg',
                'mpv', 'vlc', 'zip', 'unzip', '7z', 'bzip2', 'smbclient']:
    assert (root / 'usr/bin' / command).exists(), command
for name in ['panfrost_icd.json', 'lvp_icd.json']:
    assert (root / 'usr/share/vulkan/icd.d' / name).is_file(), name
assert 'LANG=zh_CN.UTF-8' in (root / 'etc/default/locale').read_text()
assert 'PAN_I_WANT_A_BROKEN_VULKAN_DRIVER' not in (root / 'etc/environment').read_text()
assert list((root / 'usr/share/locale/zh_CN/LC_MESSAGES').glob('plasma*.mo'))
assert list((root / 'usr/lib/libreoffice/share/registry/res').glob('*zh-CN*'))
print(json.dumps(dict(required_count=len(required), installed_count=len(installed),
                     required_packages={p: installed.get(p, {'provider': providers.get(p)}) for p in required},
                     chinese_locale=True, libreoffice_chinese=True,
                     plasma_chinese=True, panvk_globally_enabled=False), indent=2))
