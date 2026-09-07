#!/usr/bin/env python3
"""Exercise real Git checkouts, including Windows native symbolic links."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_line_endings as checker


class LineEndingsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='git-lf-regression-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.root_patch = patch.object(checker, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        checker.git('init', '--quiet', '--object-format=sha1')
        checker.git('config', 'core.autocrlf', 'false')
        self.stage('.gitattributes', b'* text=auto eol=lf\n*.bin binary\n*.cmd text eol=lf\n')
        self.stage('boot.cmd', b'echo boot\nbooti\n')
        self.stage('firmware.bin', b'\0\xff\r\n\x80\n')
        self.stage('links/boot', b'../boot.cmd', '120000')

    def stage(self, name, data, mode='100644'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        # Bypass clean filters so the negative cases contain actual bad blobs.
        oid = checker.git('hash-object', '-w', '--stdin', input=data).decode().strip()
        checker.git('update-index', '--add', '--cacheinfo', mode, oid, name)

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            checker.main()

    def test_native_and_plain_file_links(self):
        for setting in ('true', 'false'):
            with self.subTest(symlinks=setting):
                checker.git('config', 'core.symlinks', setting)
                self.check()

    def test_crlf_blob_is_rejected(self):
        self.stage('boot.cmd', b'echo boot\r\nbooti\r\n')
        with self.assertRaisesRegex(RuntimeError, 'Non-LF text in Git index'):
            self.check()

    def test_checkout_crlf_conversion_is_rejected(self):
        self.stage('.gitattributes', b'* text=auto eol=lf\n*.bin binary\n*.cmd text eol=crlf\n')
        with self.assertRaisesRegex(RuntimeError, 'Git checkout changed bytes: boot.cmd'):
            self.check()

    def test_changed_native_link_is_rejected(self):
        original_git = checker.git

        def corrupt_checkout(*args, **kwargs):
            result = original_git(*args, **kwargs)
            if 'checkout-index' in args:
                prefix = next(arg.removeprefix('--prefix=') for arg in args
                              if arg.startswith('--prefix='))
                link = Path(prefix) / 'links/boot'
                link.unlink()
                os.symlink('../wrong.cmd', link)
            return result

        checker.git('config', 'core.symlinks', 'true')
        with patch.object(checker, 'git', side_effect=corrupt_checkout):
            with self.assertRaisesRegex(RuntimeError, 'Git checkout changed'):
                self.check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
