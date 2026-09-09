#!/usr/bin/env python3
"""Execute the ARM provisioning code against sparse eMMC fixtures."""
import argparse,json,pathlib,struct,subprocess,tempfile,zlib

M=1024*1024;ENV=180*M;BOOT=730*M;ROOT=1954*M

def read_at(path,off,size):
    with path.open('rb') as f:f.seek(off);return f.read(size)

def fixture(path,sectors,corrupt=None,log_block=2):
    ept=bytearray(4096)
    struct.pack_into('<4s12sII',ept,0,b'MPT\0',b'01.00.00\0',3,0)
    for i,(name,off,size) in enumerate([(b'env',ENV,8*M),(b'system',BOOT,1024*M),(b'data',ROOT,sectors*512-ROOT)]):
        struct.pack_into('<16sQQII',ept,24+i*40,name,size,off,0,0)
    if corrupt=='boot-offset':struct.pack_into('<Q',ept,24+40+24,BOOT+M)
    if corrupt=='data-offset':struct.pack_into('<Q',ept,24+80+24,ROOT+M)
    if corrupt=='root-high':ept[24+80+20]^=1
    if corrupt=='root-low':struct.pack_into('<I',ept,24+80+16,12345)
    if corrupt=='ept':ept[0]=0
    env=b'bootcmd=run storeboot\0serial=TEST_ONLY\0upgrade_step=1\0storeboot=echo bootstrap\0\0'
    env=env.ljust(65532,b'\0');env=struct.pack('<I',zlib.crc32(env))+env
    if corrupt=='env':env=bytes([env[0]^1])+env[1:]
    fat=bytearray(512);fat[71:82]=b'W103D_BOOT ';fat[82:90]=b'FAT32   ';fat[510:512]=b'\x55\xaa'
    root=bytearray(1024);root[56:58]=b'\x53\xef';root[120:131]=b'W103D_ROOT\0'
    struct.pack_into('<I',root,4,(8*1024**3)>>(10+log_block))
    struct.pack_into('<I',root,24,log_block)
    if corrupt=='fs-high':
        struct.pack_into('<I',root,96,0x80)
        struct.pack_into('<I',root,336,1)
    if corrupt=='fs-too-large':struct.pack_into('<I',root,4,((sectors-ROOT//512)>>(log_block+1))+1)
    if corrupt=='fs-zero':struct.pack_into('<I',root,4,0)
    if corrupt=='fs-bad-block':struct.pack_into('<I',root,24,32)
    if corrupt=='boot-label':fat[71]=0
    if corrupt=='root-label':root[120]=0
    if corrupt=='root':root[56]=0
    with path.open('wb') as f:
        f.truncate(sectors*512)
        for off,data in [(0,b'FIP_RESERVED_PREFIX'.ljust(440,b'!')),(512,b'FIP-MUST-STAY'),(36*M,ept),(ENV,env),(BOOT,fat),(ROOT+1024,root)]:
            f.seek(off);f.write(data)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    exe=a.output/'bootstrap-test'
    subprocess.run(['clang','--target=arm-linux-gnueabi','-march=armv7-a','-marm','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector','-nostdlib','-static','-fuse-ld=lld','-Wl,--build-id=none','-Wl,-e,_start','-DTEST_HOST',str(pathlib.Path(__file__).with_name('bootstrap.c')),'-o',str(exe)],check=True)
    minimum=ROOT//512 + 8*1024**3//512
    valid=[minimum,24000000,28000000,30535680,31277056,33554432,
           56000000,60620800,61071360,67108864,122142720,250000000,4294967295]
    cases=[(n,None,None) for n in valid]
    cases += [(61071360,c,None) for c in ['boot-offset','data-offset','root-high','root-low','ept','env','boot-label','root-label','root','fs-high','fs-too-large','fs-zero','fs-bad-block']]
    cases += [(n,'too-small',None) for n in [ROOT//512,ROOT//512+1,16000000,minimum-1]]
    cases += [(61071360,'capacity',s) for s in ['0','-1','invalid','61071360x','61071360:0','61071360\ninvalid','61071360\n\n','4294967296','18446744073709551616']]
    cases += [(61071360,None,'61071360\n')]
    results=[]
    with tempfile.TemporaryDirectory(dir=a.output) as tmp:
        path=pathlib.Path(tmp)/'emmc.img'
        for sectors,corrupt,argument in cases:
            fixture(path,sectors,corrupt)
            areas=[(0,4096),(36*M,4096),(ENV,65536),(BOOT,512),(ROOT+1024,1024)]
            before=[read_at(path,*area) for area in areas]
            args=['qemu-arm-static',str(exe),str(path),argument or str(sectors)]
            r=subprocess.run(args,capture_output=True,text=True,timeout=15)
            if corrupt:
                assert r.returncode==1,(sectors,corrupt,r.stdout,r.stderr)
                assert before==[read_at(path,*area) for area in areas]
            else:
                assert r.returncode==0,(sectors,r.stdout,r.stderr)
                after=read_at(path,0,4096)
                assert after[:440]==before[0][:440] and after[512:]==before[0][512:]
                assert struct.unpack_from('<II',after,454)==(BOOT//512,2097152)
                assert struct.unpack_from('<II',after,470)==(ROOT//512,sectors-ROOT//512)
                assert before[1]==read_at(path,36*M,4096)
                assert before[3:]==[read_at(path,*area) for area in areas[3:]]
                env=read_at(path,ENV,65536)
                assert struct.unpack_from('<I',env)[0]==zlib.crc32(env[4:])
                assert b'serial=TEST_ONLY\0' in env
                assert b'6.18.49-v1\0' in env
                r2=subprocess.run(args,capture_output=True,timeout=15)
                assert r2.returncode==0 and read_at(path,0,4096)==after and read_at(path,ENV,65536)==env
            results.append(dict(sectors=sectors,case=corrupt or 'success-and-idempotence',argument=argument,passed=True))
        for log in [0,1,6]:
            fixture(path,minimum,log_block=log)
            r=subprocess.run(['qemu-arm-static',str(exe),str(path),str(minimum)],capture_output=True,text=True,timeout=15)
            assert r.returncode==0,(log,r.stdout,r.stderr)
            results.append(dict(case='exact-fit-block-size',block_bytes=1024<<log,passed=True))
    (a.output/'bootstrap-tests.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(dict(passed=len(results),valid_capacities=len(valid),rejected_cases=sum(c[1] is not None for c in cases))))

if __name__=='__main__':main()
