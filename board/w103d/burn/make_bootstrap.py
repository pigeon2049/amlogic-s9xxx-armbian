#!/usr/bin/env python3
"""Replace only the initramfs in the reference Android v0 boot container."""
import argparse, gzip, hashlib, json, pathlib, stat, struct

def cpio_entry(name, payload, mode, inode, rmajor=0, rminor=0):
    name=name.encode()+b'\0'
    fields=[inode,mode,0,0,1,0,len(payload),0,0,rmajor,rminor,len(name),0]
    data=b'070701'+b''.join(f'{x:08x}'.encode() for x in fields)+name
    data+=bytes((-len(data))%4)
    data+=payload
    return data+bytes((-len(payload))%4)

def build(original, executable):
    assert original[:8]==b'ANDROID!'
    ksize,kaddr,rsize,raddr,ssize,saddr,tags,page,version=struct.unpack_from('<9I',original,8)
    assert page==2048 and version==0 and ssize==0
    kernel=original[page:page+ksize]
    assert kernel[:4]==bytes.fromhex('27051956') # original ARM32 uImage
    assert executable[:4]==b'\x7fELF' and struct.unpack_from('<H',executable,18)[0]==40
    cpio=b''
    for i,name in enumerate(['dev','proc','sys'],1):
        cpio+=cpio_entry(name,b'',stat.S_IFDIR|0o755,i)
    cpio+=cpio_entry('dev/console',b'',stat.S_IFCHR|0o600,4,5,1)
    cpio+=cpio_entry('dev/null',b'',stat.S_IFCHR|0o666,5,1,3)
    cpio+=cpio_entry('init',executable,stat.S_IFREG|0o755,6)
    cpio+=cpio_entry('TRAILER!!!',b'',0,7)
    cpio+=bytes((-len(cpio))%512)
    ramdisk=gzip.compress(cpio,compresslevel=9,mtime=0)
    header=bytearray(original[:page])
    struct.pack_into('<I',header,16,len(ramdisk))
    h=hashlib.sha1()
    for part in [kernel,ramdisk,b'']:h.update(part);h.update(struct.pack('<I',len(part)))
    header[576:608]=h.digest()+bytes(12)
    result=bytes(header)+kernel+bytes((-len(kernel))%page)+ramdisk+bytes((-len(ramdisk))%page)
    assert len(result)<=16*1024**2
    assert result[page:page+ksize]==kernel
    return result,dict(bootstrap_kernel='reference ARM32 vendor Linux 4.9.113; provisioning only',kernel_sha256=hashlib.sha256(kernel).hexdigest(),init_sha256=hashlib.sha256(executable).hexdigest(),ramdisk_bytes=len(ramdisk),boot_bytes=len(result),runtime_release='6.18.49-ophub')

def main():
    p=argparse.ArgumentParser();p.add_argument('reference',type=pathlib.Path);p.add_argument('init',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
    data,manifest=build(a.reference.read_bytes(),a.init.read_bytes())
    a.output.write_bytes(data)
    a.output.with_suffix('.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest))

if __name__=='__main__':main()
