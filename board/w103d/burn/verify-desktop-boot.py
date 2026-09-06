#!/usr/bin/env python3
"""Boot a disposable QEMU virt snapshot; check SSH and the pairing program's linkage.

This does not emulate Bluetooth, board firmware or the USB Burning bootstrap.
Requires pexpect, qemu-system-aarch64, ssh, and the matched runtime kernel/initrd.
"""
import argparse
import json
from pathlib import Path
import pexpect

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('work', type=Path)
p.add_argument('--kernel', required=True)
p.add_argument('--initrd', required=True)
p.add_argument('--ssh-port', type=int, default=22022)
a = p.parse_args()
work = a.work.resolve(strict=True)
report = work / 'checks/qemu-clean-firstboot.json'
assert not report.exists(), 'Use a new check directory or archive the prior report.'
args = ['-M', 'virt', '-cpu', 'cortex-a53', '-smp', '4', '-m', '2048',
        '-accel', 'tcg,thread=multi', '-kernel', a.kernel, '-initrd', a.initrd,
        '-append', 'root=/dev/vda rw console=ttyAMA0,115200 net.ifnames=0 systemd.unit=multi-user.target',
        '-drive', f'file={work}/rootfs.raw,format=raw,if=none,id=root,snapshot=on',
        '-device', 'virtio-blk-pci,drive=root',
        '-drive', f'file={work}/bootfs.raw,format=raw,if=none,id=boot,snapshot=on',
        '-device', 'virtio-blk-pci,drive=boot',
        '-netdev', f'user,id=net,hostfwd=tcp:127.0.0.1:{a.ssh_port}-:22',
        '-device', 'virtio-net-pci,netdev=net,romfile=',
        '-nographic', '-monitor', 'none', '-no-reboot']
with (work / 'checks/qemu-clean-firstboot.log').open('w') as log:
    vm = pexpect.spawn('qemu-system-aarch64', args, encoding='utf-8',
                       codec_errors='replace', timeout=180)
    vm.logfile = log
    try:
        vm.expect('armbian login:', timeout=300)
        vm.sendline('root')
        vm.expect(['Password:', '密码：'])
        vm.sendline('1234')
        vm.expect(r'root@armbian:.*#', timeout=90)
        command = (
            "test \"$(uname -r)\" = 6.18.49-ophub && systemctl is-active ssh && "
            "test ! -e /root/.not_logged_in_yet && "
            "ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub && "
            "test \"$(dpkg-query -W -f='${Version}' bluedevil)\" = '4:6.3.4-2+w103d1' && "
            "test -z \"$(dpkg --audit)\" && "
            "LC_ALL=C apt-cache policy bluedevil | grep -F 'Candidate: 4:6.3.4-2+w103d1' && "
            "dbus-run-session -- env QT_QPA_PLATFORM=offscreen LD_BIND_NOW=1 "
            "/usr/bin/bluedevil-wizard --version && echo __PAIRING_BOOT_OK__"
        )
        vm.sendline(command)
        vm.expect(r'[\r\n]+__PAIRING_BOOT_OK__[\r\n]+', timeout=120)
        assert 'bluedevilwizard 6.3.4-w103d1' in vm.before
        print('Clean boot, kernel, dpkg, APT candidate and wizard linkage passed.', flush=True)
        for user in ['root', 'armbian']:
            ssh = pexpect.spawn('ssh', ['-o', 'StrictHostKeyChecking=no', '-o',
                'UserKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15',
                '-p', str(a.ssh_port), user + '@127.0.0.1',
                f'test "$(id -un)" = {user} && echo __SSH_OK__'],
                encoding='utf-8', timeout=60)
            ssh.logfile = log
            try:
                ssh.expect('[Pp]assword:')
                ssh.sendline('1234')
                ssh.expect('__SSH_OK__')
                ssh.expect(pexpect.EOF)
                ssh.close()
                assert ssh.exitstatus == 0
            finally:
                ssh.close(force=True)
            print(user + ' SSH login passed.', flush=True)
        image = json.loads((work / 'checks/final-package.json').read_text())
        report.write_text(json.dumps(dict(clean_first_boot=True, ssh_hostkeys_generated=True,
            root_ssh=True, armbian_ssh=True, no_first_login_wizard=True, snapshot_only=True,
            runtime_release='6.18.49-ophub', wizard_version='6.3.4-w103d1',
            wizard_dynamic_linkage=True, apt_candidate='4:6.3.4-2+w103d1', dpkg_audit_clean=True,
            emulated_platform='QEMU virt', hardware_bluetooth_emulated=False,
            board_flashed=False, image_sha256=image['sha256']), indent=2) + '\n')
    finally:
        vm.close(force=True)
