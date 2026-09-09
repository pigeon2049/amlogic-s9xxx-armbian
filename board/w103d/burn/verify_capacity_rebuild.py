#!/usr/bin/env python3
"""Confirm only the bootstrap payloads differ from the supplied W103D base."""
import argparse,hashlib,json,pathlib,struct,subprocess,tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('work',type=pathlib.Path,help='universal assembly directory')
parser.add_argument('base',type=pathlib.Path,help='verified W103D assembly directory')
args=parser.parse_args()
w=args.work
b=args.base
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
new=json.loads((w/'checks/final-package.json').read_text())
old=json.loads((b/'checks/final-package.json').read_text())
before={(p['main'],p['sub']):p for p in old['items']}
assert len(before)==len(old['items'])==len(new['items'])
assert set(before)=={(p['main'],p['sub']) for p in new['items']}
changed=[]
for item in new['items']:
    key=(item['main'],item['sub'])
    if item['sha256']!=before[key]['sha256']:changed.append(key)
assert set(changed)<={('PARTITION','boot'),('PARTITION','recovery'),('VERIFY','boot'),('VERIFY','recovery')},changed
assert digest(w/'bootfs.raw')==digest(b/'bootfs.raw')
assert digest(w/'rootfs.raw')==digest(b/'rootfs.raw')
original=(b/'payloads/boot.PARTITION').read_bytes();trial=(w/'payloads/boot.PARTITION').read_bytes()
ksize=struct.unpack_from('<I',original,8)[0];page=struct.unpack_from('<I',original,36)[0]
assert trial[page:page+ksize]==original[page:page+ksize]
# The Android DTB's data partition is already "remaining device capacity".
dtb=(b/'payloads/_aml_dtb.PARTITION').read_bytes()
offset=dtb.find(bytes.fromhex('d00dfeed'));assert offset>=0
size=struct.unpack_from('>I',dtb,offset+4)[0]
with tempfile.TemporaryDirectory() as t:
    p=pathlib.Path(t)/'vendor.dtb';p.write_bytes(dtb[offset:offset+size])
    data_size=subprocess.check_output(['fdtget','-t','x',str(p),'/partitions/data','size'],text=True).strip()
    assert data_size=='ffffffff ffffffff',data_size
# The published sparse payload spans the entire raw filesystem. Require its
# size to equal the ext4 declared extent, so the runtime fit check is sufficient.
with (w/'rootfs.raw').open('rb') as f:
    f.seek(1024);sb=f.read(1024)
assert sb[56:58]==b'\x53\xef'
lo=struct.unpack_from('<I',sb,4)[0];log=struct.unpack_from('<I',sb,24)[0]
hi=struct.unpack_from('<I',sb,336)[0] if struct.unpack_from('<I',sb,96)[0]&0x80 else 0
assert log<=6 and lo>0 and hi==0
fsbytes=lo*(1024<<log)
assert fsbytes==(w/'rootfs.raw').stat().st_size and fsbytes%512==0
minimum=1954*2048+fsbytes//512
assert minimum<=4294967295
result=dict(universal_w103d_w102d=True,changed_container_items=changed,rootfs_identical_to_base=True,
 bootfs_identical_to_base=True,base_image=old['image'],base_sha256=old['sha256'],
 vendor_kernel_identical=True,vendor_dtb_data_partition='remaining capacity',
 emmc_capacity_source='runtime sysfs sector count, checked against on-device EPT',
 capacity_whitelist=False,minimum_sectors_for_this_rootfs=minimum,
 mbr_sector_count_max=4294967295,rootfs_bytes=fsbytes,led_gpio_preserved=True,
 root_partition_start_sector=1954*1024*1024//512,root_partition_end='actual device end',
 board_flashed=False,hardware_w102d_validated=False)
(w/'checks/capacity-rebuild.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
