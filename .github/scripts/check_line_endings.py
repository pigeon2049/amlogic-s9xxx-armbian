#!/usr/bin/env python3
"""Verify LF blobs, checkout contents/link targets and exact archive bytes."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def git(*args, **kwargs):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], **kwargs)


def blob_id(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def checkout_blob(path, mode, oid):
    if not path.is_symlink():
        # With core.symlinks=false Git writes the link's blob as a plain file.
        return path.read_bytes()
    if mode != b'120000':
        raise RuntimeError('Unexpected symbolic link: ' + str(path))
    data = os.fsencode(os.readlink(path))
    if os.name == 'nt':
        # Git for Windows converts POSIX separators when creating native links.
        # Compare the exact expected Windows target, not a normalized pair that
        # could conceal other target changes. Archive links remain byte-exact.
        source = git('cat-file', 'blob', oid)
        if data != source.replace(b'/', b'\\'):
            raise RuntimeError('Git checkout changed symbolic link target: ' + str(path))
        return source
    return data


def main():
    if git('rev-parse', '--show-object-format').strip() != b'sha1':
        raise RuntimeError('Update blob hashing for this repository object format')
    entries = {}
    for record in git('ls-files', '--stage', '-z').split(b'\0'):
        if not record:
            continue
        info, path = record.split(b'\t', 1)
        mode, oid, stage = info.split()
        if stage != b'0' or mode == b'160000':
            raise RuntimeError('Requires a resolved index without submodules')
        entries[os.fsdecode(path)] = (mode, oid.decode())
    for record in git('ls-files', '--eol', '-z').split(b'\0'):
        if record.startswith((b'i/crlf', b'i/mixed')):
            raise RuntimeError('Non-LF text in Git index: ' + os.fsdecode(record))

    # Test the staged tree as well as committed trees without modifying the
    # caller's checkout, Git configuration or repository history.
    tree = git('write-tree').decode().strip()
    settings = ['-c', 'core.autocrlf=true', '-c', 'core.eol=crlf']
    with tempfile.TemporaryDirectory(prefix='w103d-git-lf-') as temp:
        target = Path(temp).resolve()
        if target.parent != Path(tempfile.gettempdir()).resolve():
            raise RuntimeError('Unexpected temporary checkout location')
        git(*settings, 'checkout-index', '--all', '--prefix=' + target.as_posix() + '/')
        for name, (mode, oid) in entries.items():
            path = target / name
            data = checkout_blob(path, mode, oid)
            if blob_id(data) != oid:
                raise RuntimeError('Git checkout changed bytes: ' + name)

    archive = git(*settings, 'archive', '--format=tar', tree)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for item in stream:
            if item.isdir():
                continue
            data = os.fsencode(item.linkname) if item.issym() else stream.extractfile(item).read()
            if item.name not in entries or blob_id(data) != entries[item.name][1]:
                raise RuntimeError('git archive changed bytes: ' + item.name)
            count += 1
    if count != len(entries):
        raise RuntimeError('Archive omitted tracked files; review export attributes')
    print(f'PASS: {count} tracked entries verified with core.autocrlf=true and '
          'core.eol=crlf; index text is LF; checkout files and archive entries '
          'are byte-identical; native link targets match platform separators.')


if __name__ == '__main__':
    main()
