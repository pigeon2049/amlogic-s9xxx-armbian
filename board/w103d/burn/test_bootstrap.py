#!/usr/bin/env python3
"""Run the ARM bootstrap's provisioning code under qemu-user on sparse fixtures."""
import argparse, hashlib, json, pathlib, struct, subprocess, tempfile, zlib

M=1024*1024
SIZE=31037849600
ENV=180*M
BOOT=730*M
ROOT=1954*M

def fixture(path, corrupt=None):
    ept=bytearray(4096)
    struct.pack_into('<4s12sII',ept,0,b'MPT\0',b'01.00.00\0',3,0)
    for i,(name,off,size) in enumerate([(b'env',ENV,8*M),(b'system',BOOT,1024*M),(b'data',ROOT,SIZE-ROOT)]):
        struct.pack_into('<16sQQII',ept,24+40*i,name,size,off,0,0)
    if corrupt=='ept':struct.pack_into('<Q',ept,24+40+24,BOOT+M)
    env=b'bootcmd=run storeboot\0serial=TEST_ONLY\0upgrade_step=1\0storeboot=echo bootstrap\0\0'
    env=env.ljust(65532,b'\0');env=struct.pack('<I',zlib.crc32(env))+env
    if corrupt=='env':env=bytes([env[0]^1])+env[1:]
    fat=bytearray(512);fat[71:82]=b'W103D_BOOT ';fat[82:90]=b'FAT32   ';fat[510:512]=b'\x55\xaa'
    root=bytearray(1024);root[56:58]=b'\x53\xef';root[120:131]=b'W103D_ROOT\0'
    if corrupt=='root':root[56]=0
    with path.open('wb') as f:
        f.truncate(SIZE)
        for off,data in [(0,b'FIP_RESERVED_PREFIX'.ljust(440,b'!')),(512,b'FIP-MUST-STAY'),(36*M,ept),(ENV,env),(BOOT,fat),(ROOT+1024,root)]:
            f.seek(off);f.write(data)

def read_at(path,off,size):
    with path.open('rb') as f:f.seek(off);return f.read(size)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    source=pathlib.Path(__file__).with_name('bootstrap.c')
    a.output.mkdir(parents=True,exist_ok=True)
    exe=a.output/'bootstrap-test'
    cmd=['clang','--target=arm-linux-gnueabi','-march=armv7-a','-marm','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-nostdlib','-static','-fuse-ld=lld','-Wl,--build-id=none','-Wl,-e,_start','-DTEST_HOST',str(source),'-o',str(exe)]
    subprocess.run(cmd,check=True)
    results=[]
    with tempfile.TemporaryDirectory(dir=a.output) as tmp:
        path=pathlib.Path(tmp)/'emmc.img'
        for corrupt in [None,'ept','env','root']:
            fixture(path,corrupt)
            before=read_at(path,0,4096);env_before=read_at(path,ENV,65536)
            r=subprocess.run(['qemu-arm-static',str(exe),str(path)],capture_output=True,text=True,timeout=15)
            if corrupt:
                assert r.returncode==1,(corrupt,r.stdout,r.stderr)
                assert read_at(path,0,4096)==before and read_at(path,ENV,65536)==env_before
            else:
                assert r.returncode==0,(r.stdout,r.stderr)
                after=read_at(path,0,4096)
                assert after[:440]==before[:440] and after[512:]==before[512:]
                assert after[510:512]==b'\x55\xaa'
                assert struct.unpack_from('<II',after,454)==(BOOT//512,1024*M//512)
                assert struct.unpack_from('<II',after,470)==(ROOT//512,(SIZE-ROOT)//512)
                env=read_at(path,ENV,65536)
                assert struct.unpack_from('<I',env)[0]==zlib.crc32(env[4:])
                assert b'serial=TEST_ONLY\0' in env and b'bootcmd=run w103d_emmc;' in env
                r2=subprocess.run(['qemu-arm-static',str(exe),str(path)],capture_output=True,timeout=15)
                assert r2.returncode==0 and read_at(path,0,4096)==after and read_at(path,ENV,65536)==env
            results.append({'case':corrupt or 'success-and-idempotence','passed':True})
    (a.output/'bootstrap-tests.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))

if __name__=='__main__':main()
