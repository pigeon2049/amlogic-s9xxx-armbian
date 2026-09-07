#!/usr/bin/env python3
"""Validate the actual U-Boot script, including line endings and legacy CRCs."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib


def source_bytes(path):
    data = Path(path).read_bytes()
    if not data or b'\r' in data or b'\0' in data or data.startswith(b'\xef\xbb\xbf'):
        raise ValueError('U-Boot script must use LF, without CR, NUL or BOM')
    data.decode('utf-8')
    if not data.endswith(b'\n'):
        raise ValueError('U-Boot script must end with LF')
    return data


def verify_legacy(data, expected):
    if len(data) < 72:
        raise ValueError('Truncated U-Boot script image')
    magic, hcrc, stamp, size, load, entry, dcrc, os_id, arch, kind, comp, name = struct.unpack('>7I4B32s', data[:64])
    if magic != 0x27051956 or (os_id, arch, kind, comp) != (5, 2, 6, 0):
        raise ValueError('Expected uncompressed ARM/Linux legacy script image')
    header = bytearray(data[:64]); header[4:8] = b'\0' * 4
    payload = data[64:]
    if zlib.crc32(header) != hcrc or size != len(payload) or zlib.crc32(payload) != dcrc:
        raise ValueError('U-Boot script header/data CRC or length mismatch')
    script_size, end = struct.unpack('>II', payload[:8])
    if end != 0 or script_size != len(expected) or payload[8:] != expected:
        raise ValueError('Compiled U-Boot script does not match the validated LF source')
    return {'script_bytes': script_size, 'lf_only': True, 'header_crc_valid': True,
            'data_crc_valid': True, 'compiled_source_match': True}


def verify_directory(boot, source=None):
    source = source or Path(__file__).with_name('emmc_autoscript.cmd')
    expected = source_bytes(source)
    if source_bytes(Path(boot) / 'emmc_autoscript.cmd') != expected:
        raise ValueError('Boot filesystem script source differs from the build source')
    return verify_legacy((Path(boot) / 'emmc_autoscript').read_bytes(), expected)


def verify_fat(raw):
    with tempfile.TemporaryDirectory(prefix='w103d-boot-script-') as temp:
        for name in ('emmc_autoscript', 'emmc_autoscript.cmd'):
            subprocess.run(['mcopy', '-i', str(raw), '::/' + name, str(Path(temp) / name)], check=True)
        return verify_directory(temp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--source', type=Path)
    group.add_argument('--boot-dir', type=Path)
    group.add_argument('--fat-image', type=Path)
    args = parser.parse_args()
    if args.source:
        result = {'source_bytes': len(source_bytes(args.source)), 'lf_only': True}
    elif args.boot_dir:
        result = verify_directory(args.boot_dir)
    else:
        result = verify_fat(args.fat_image)
    print(json.dumps(result, indent=2))
