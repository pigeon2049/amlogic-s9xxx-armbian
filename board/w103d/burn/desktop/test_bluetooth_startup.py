#!/usr/bin/env python3
"""Regress the saved-off KDE startup case using the real offline configurator."""
import configparser
import importlib.util
from pathlib import Path
import tempfile
import unittest


def load(filename):
    spec = importlib.util.spec_from_file_location(filename, Path(__file__).with_name(filename + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


configure = load('configure-bluetooth').configure
verify = load('verify-bluetooth').verify


class BluetoothStartup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='w103d-bt-startup-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        unit = self.root / 'usr/lib/systemd/system/bluetooth.service'
        unit.parent.mkdir(parents=True)
        unit.write_text('[Service]\nExecStart=/usr/libexec/bluetooth/bluetoothd\n'
                        '[Install]\nWantedBy=bluetooth.target\nAlias=dbus-org.bluez.service\n')
        (self.root / 'home/armbian/.config').mkdir(parents=True)
        (self.root / 'etc/bluetooth').mkdir(parents=True)
        (self.root / 'etc/bluetooth/main.conf').write_text('[General]\nName=KeepName\n[Policy]\nAutoEnable=false\n')

    def test_saved_off_state_and_bonds_survive_configuration(self):
        path = self.root / 'home/armbian/.config/bluedevilglobalrc'
        path.write_text('[Global]\nlaunchState=disable\nbluetoothBlocked=true\n'
                        '[General]\nlaunchState=enable\nbluetoothBlocked=false\nKeepMe=yes\n'
                        '[Adapters]\n00:11:22:33:44:55_powered=false\n'
                        '[Devices]\nconnectedDevices=00:11:22:33:44:66\n')
        bond = self.root / 'var/lib/bluetooth/test-adapter/test-device/info'
        bond.parent.mkdir(parents=True)
        bond.write_bytes(b'test bond sentinel')
        configure(self.root)
        first = path.read_bytes()
        configure(self.root)
        self.assertEqual(path.read_bytes(), first)
        config = configparser.RawConfigParser(delimiters=('=',))
        config.read(path)
        self.assertEqual(config.get('Global', 'launchState'), 'enable')
        self.assertFalse(config.getboolean('Global', 'bluetoothBlocked'))
        self.assertFalse(config.has_option('General', 'launchState'))
        self.assertEqual(config.get('General', 'KeepMe'), 'yes')
        self.assertEqual(config.get('Devices', 'connectedDevices'), '00:11:22:33:44:66')
        self.assertEqual(bond.read_bytes(), b'test bond sentinel')
        with self.assertRaises(AssertionError):
            verify(self.root)  # Live state must never pass shipping validation.

    def test_clean_image_and_reject_remember_policy(self):
        configure(self.root)
        self.assertTrue(verify(self.root)['bluez_auto_enable'])
        path = self.root / 'home/armbian/.config/bluedevilglobalrc'
        path.write_text(path.read_text().replace('launchState=enable', 'launchState=remember'))
        with self.assertRaises(AssertionError):
            verify(self.root)

    def test_reject_saved_rfkill_state(self):
        configure(self.root)
        path = self.root / 'var/lib/systemd/rfkill/platform-test:bluetooth'
        path.parent.mkdir(parents=True)
        path.write_text('1')
        with self.assertRaises(AssertionError):
            verify(self.root)

    def test_reject_v7_wrong_group(self):
        configure(self.root)
        path = self.root / 'home/armbian/.config/bluedevilglobalrc'
        path.write_text(path.read_text().replace('[Global]', '[General]'))
        with self.assertRaises(configparser.NoSectionError):
            verify(self.root)


if __name__ == '__main__':
    unittest.main()
