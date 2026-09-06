#!/usr/bin/env python3
"""Confirm only the bootstrap payloads differ from the original v5 package."""
import argparse,hashlib,json,pathlib,struct,subprocess,tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('work',type=pathlib.Path,help='W102D assembly directory')
parser.add_argument('base',type=pathlib.Path,help='verified W103D v5 assembly directory')
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
assert set(changed)=={('PARTITION','boot'),('PARTITION','recovery'),('VERIFY','boot'),('VERIFY','recovery')},changed
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
result=dict(capacity_only_trial=True,changed_container_items=changed,rootfs_identical_to_v5=True,
 bootfs_identical_to_v5=True,vendor_kernel_identical=True,vendor_dtb_data_partition='remaining capacity',
 emmc_capacity_source='runtime sysfs sector count, checked against on-device EPT',
 accepted_sectors_min=28000000,accepted_sectors_max=33554432,
 root_partition_start_sector=1954*1024*1024//512,root_partition_end='actual device end',
 board_flashed=False,hardware_w102d_validated=False)
(w/'checks/capacity-only.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
