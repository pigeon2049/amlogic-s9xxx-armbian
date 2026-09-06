#!/usr/bin/env python3
"""Repack the exact Debian baseline, checking payload differences and ELF imports."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('original', type=Path)
p.add_argument('wizard', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
original = a.original.resolve()
wizard = a.wizard.resolve()
output = a.output.resolve()
output.mkdir(parents=True, exist_ok=True)
stage = output / 'package'
if stage.exists():
    raise SystemExit(f'Refusing to overwrite existing package staging directory: {stage}')
fields = subprocess.check_output(['dpkg-deb', '-f', str(original), 'Package', 'Version', 'Architecture'], text=True)
assert fields.splitlines() == ['Package: bluedevil', 'Version: 4:6.3.4-2', 'Architecture: arm64'], fields
subprocess.run(['dpkg-deb', '-R', str(original), str(stage)], check=True)

def hashes():
    return {str(f.relative_to(stage)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in stage.rglob('*') if f.is_file() and not f.is_symlink()
            and 'DEBIAN' not in f.relative_to(stage).parts}

before = hashes()
target = stage / 'usr/bin/bluedevil-wizard'
old_symbols = subprocess.check_output(['nm', '-D', '-C', str(target)], text=True)
new_symbols = subprocess.check_output(['nm', '-D', '-C', str(wizard)], text=True)
assert 'BluezQt::Device::disconnectFromDevice()' in old_symbols
assert 'BluezQt::Device::disconnectFromDevice()' not in new_symbols
elf = subprocess.check_output(['readelf', '-h', str(wizard)], text=True)
assert 'AArch64' in elf and 'ELF64' in elf
target.write_bytes(wizard.read_bytes())
target.chmod(0o755)
subprocess.run(['aarch64-linux-gnu-strip', '--strip-unneeded', str(target)], check=True)
control = stage / 'DEBIAN/control'
text = control.read_text().replace('Version: 4:6.3.4-2\n', 'Version: 4:6.3.4-2+w103d1\n')
control.write_text(text)
after = hashes()
changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
assert changed == ['usr/bin/bluedevil-wizard'], changed
md5 = stage / 'DEBIAN/md5sums'
md5.write_text(''.join(f'{hashlib.md5((stage / name).read_bytes()).hexdigest()}  {name}\n' for name in sorted(after)))
deb = output / 'bluedevil_6.3.4-2+w103d1_arm64.deb'
subprocess.run(['dpkg-deb', '--root-owner-group', '-b', str(stage), str(deb)], check=True)
report = {'baseline': fields, 'changed_payload_files': changed,
          'upstream_commit': 'dff9c79ca81370ed72f672b45ac39ec3d1c09875',
          'old_disconnect_import': True, 'new_disconnect_import': False,
          'original_wizard_sha256': before['usr/bin/bluedevil-wizard'],
          'package_sha256': hashlib.sha256(deb.read_bytes()).hexdigest(),
          'wizard_sha256': after['usr/bin/bluedevil-wizard']}
(output / 'package-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
