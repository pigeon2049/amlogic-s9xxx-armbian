#!/usr/bin/env python3
"""Install/verify the exact board-tested probe and TX-reporting module pair."""
import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import tempfile

MANIFEST = json.loads(Path(__file__).with_name('wireless-modules.json').read_text())


def module_path(root, name):
    directory = Path(root) / 'usr/lib/modules' / MANIFEST['release']
    found = [p for p in directory.rglob(name + '.ko*')
             if p.name in [name + '.ko' + ext for ext in ('', '.xz', '.gz', '.zst')]]
    if len(found) != 1:
        raise RuntimeError(f'Expected exactly one {name} module, found {len(found)}')
    return found[0]


def validate(path, name):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix == '.xz':
        data = lzma.decompress(data)
    elif path.suffix == '.gz':
        data = gzip.decompress(data)
    elif path.suffix == '.zst':
        data = subprocess.check_output(['zstd', '-qdc', str(path)])
    if hashlib.sha256(data).hexdigest() != MANIFEST['modules'][name]['sha256']:
        raise RuntimeError(f'{name}: not the tested connection-probe/TX-reporting artifact')
    # Inspect uncompressed bytes: host libkmod builds do not all support
    # every compression format used in target module trees.
    with tempfile.NamedTemporaryFile(suffix='.ko') as module:
        module.write(data)
        module.flush()
        def field(key):
            return subprocess.check_output(['modinfo', '-F', key, module.name], text=True).strip()
        if field('vermagic').split()[0] != MANIFEST['release']:
            raise RuntimeError(f'{name}: full module release mismatch')
        required = {'cfg80211'}
        if name == 'mt7663s':
            required.update('mt76-connac-lib,btmtksdio,mt7663-usb-sdio-common,mt7615-common,mt76-sdio,mt76,mac80211'.split(','))
            if 'sdio:c*v037Ad7603*' not in field('alias').splitlines():
                raise RuntimeError('Missing MT7663S SDIO alias')
        if not required <= set(field('depends').split(',')):
            raise RuntimeError(f'{name}: required dependencies missing')
    return data


def verify(root):
    for name in MANIFEST['modules']:
        validate(module_path(root, name), name)
    return MANIFEST


def install(root, mt7663s, mac80211):
    root = Path(root).resolve(strict=True)
    if root == Path('/') or not root.is_mount():
        raise RuntimeError('Use an offline mounted image root')
    # Preflight the entire pair before replacing either module.
    staged = []
    for name, source in [('mt7663s', mt7663s), ('mac80211', mac80211)]:
        data = validate(source, name)
        destination = module_path(root, name)
        if destination.suffix == '.xz':
            data = lzma.compress(data)
        elif destination.suffix == '.gz':
            data = gzip.compress(data, mtime=0)
        elif destination.suffix == '.zst':
            data = subprocess.check_output(['zstd', '-q', '-c'], input=data)
        staged.append((destination, data))
    for destination, data in staged:
        destination.write_bytes(data)
        destination.chmod(0o644)
    verify(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--install', nargs=2, metavar=('MT7663S', 'MAC80211'))
    args = parser.parse_args()
    if args.install:
        install(args.root, *args.install)
    print(json.dumps(verify(args.root), indent=2))
