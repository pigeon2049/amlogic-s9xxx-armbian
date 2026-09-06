#!/usr/bin/env python3
"""Verify the tested pairing backport and absence of device bonds in a shipping root."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve(strict=True)
source = Path(__file__).resolve().parent
expected = json.loads((source / 'package-check.json').read_text())
packages = {}
for block in (root / 'var/lib/dpkg/status').read_text().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines()
                  if ': ' in line and not line.startswith(' '))
    packages[fields.get('Package')] = fields
package = packages['bluedevil']
assert package['Version'] == '4:6.3.4-2+w103d1'
assert package['Architecture'] == 'arm64'
assert package['Status'] == 'install ok installed'
wizard = root / 'usr/bin/bluedevil-wizard'
assert hashlib.sha256(wizard.read_bytes()).hexdigest() == expected['wizard_sha256']
assert wizard.stat().st_mode & 0o777 == 0o755
symbols = subprocess.check_output(['nm', '-D', '-C', str(wizard)], text=True)
assert 'BluezQt::Device::disconnectFromDevice()' not in symbols
assert (root / 'etc/apt/preferences.d/w103d-bluedevil-pairing').read_text() == (source / 'pairing.pref').read_text()
assert not list((root / 'var/lib/bluetooth').glob('*')), 'Shipping root contains Bluetooth state'
print(json.dumps(dict(version=package['Version'], wizard_sha256=expected['wizard_sha256'],
                     upstream_commit=expected['upstream_commit'], disconnect_import=False,
                     bluetooth_state_absent=True, apt_pin_priority=1001), indent=2))
