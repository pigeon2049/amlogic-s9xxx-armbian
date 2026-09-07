#!/usr/bin/env python3
"""Reject scripts that have valid uImage CRCs but invalid CRLF text."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
from boot_script import source_bytes, verify_legacy


class BootScript(unittest.TestCase):
    def test_actual_mkimage_and_crlf_regression(self):
        canonical = Path(__file__).with_name('emmc_autoscript.cmd')
        expected = source_bytes(canonical)
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for ending in ('lf', 'crlf'):
                script = temp / (ending + '.cmd')
                script.write_bytes(expected if ending == 'lf' else expected.replace(b'\n', b'\r\n'))
                image = temp / (ending + '.scr')
                subprocess.run(['mkimage', '-A', 'arm', '-O', 'linux', '-T', 'script', '-C', 'none',
                                '-n', 'W103D test', '-d', str(script), str(image)], check=True, stdout=subprocess.DEVNULL)
                data = image.read_bytes()
                if ending == 'lf':
                    self.assertTrue(verify_legacy(data, expected)['compiled_source_match'])
                    corrupt = bytearray(data); corrupt[-1] ^= 1
                    with self.assertRaisesRegex(ValueError, 'CRC'):
                        verify_legacy(corrupt, expected)
                else:
                    # mkimage happily accepts CRLF and emits correct CRCs.
                    self.assertEqual(zlib.crc32(data[64:]), struct.unpack_from('>I', data, 24)[0])
                    with self.assertRaisesRegex(ValueError, 'LF'):
                        source_bytes(script)
                    with self.assertRaisesRegex(ValueError, 'validated LF source'):
                        verify_legacy(data, expected)

    def test_reject_bom_and_missing_final_newline(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.cmd'
            for value in (b'\xef\xbb\xbfecho hi\n', b'echo hi', b'echo hi\0\n'):
                path.write_bytes(value)
                with self.assertRaises(ValueError):
                    source_bytes(path)


if __name__ == '__main__':
    unittest.main()
