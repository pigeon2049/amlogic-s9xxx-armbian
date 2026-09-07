#!/usr/bin/env python3
"""Independently verify container payloads, sparse expansion and bootstrap init."""
import argparse,gzip,hashlib,json,pathlib,struct,zlib
from boot_script import verify_fat

def hash_file(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def sparse_hash(path):
    h=hashlib.sha256();crc=0;total=0
    with path.open('rb') as f:
        magic,major,minor,hs,cs,bs,blocks,count,expected_crc=struct.unpack('<IHHHHIIII',f.read(28))
        assert (magic,major,minor,hs,cs,bs)==(0xed26ff3a,1,0,28,12,4096)
        for _ in range(count):
            kind,res,n,sz=struct.unpack('<HHII',f.read(12));length=n*bs
            assert res==0 and length>0
            if kind==0xcac1:
                assert sz==12+length
                data=f.read(length);assert len(data)==length
            elif kind==0xcac2:
                assert sz==16
                word=f.read(4);assert len(word)==4
                data=word*(length//4)
            else:raise AssertionError(f'Unexpected sparse chunk {kind:x}')
            h.update(data);crc=zlib.crc32(data,crc);total+=length
        assert total==blocks*bs and crc==expected_crc and not f.read(1)
    return h.hexdigest()

def cpio_files(data):
    result={};pos=0
    while True:
        assert data[pos:pos+6]==b'070701'
        fields=[int(data[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        n=fields[11];size=fields[6]
        name=data[pos+110:pos+110+n-1].decode()
        pos=(pos+110+n+3)&~3
        if name=='TRAILER!!!':break
        result[name]=data[pos:pos+size];pos=(pos+size+3)&~3
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('work',type=pathlib.Path);p.add_argument('--logo',type=pathlib.Path,required=True);a=p.parse_args()
    work=a.work;images=list(work.glob('*.burn.img'));assert len(images)==1
    img=images[0];payloads=work/'payloads';records=[]
    with img.open('rb') as f:
        header=f.read(64)
        crc,version,magic,size,align,count=struct.unpack_from('<IIIQII',header)
        assert version==2 and magic==0x27b51956 and size==img.stat().st_size
        assert align in (4,8,16)
        for _ in range(count):
            d=f.read(576);_,kind,cur,offset,length=struct.unpack_from('<IIQQQ',d)
            main=d[32:288].split(b'\0')[0].decode();sub=d[288:544].split(b'\0')[0].decode()
            assert offset>=64+576*count and offset+length<=size
            # The packer aligns payload starts. VERIFY text immediately follows
            # its payload, including non-aligned sparse images and small blobs.
            if main!='VERIFY':assert offset%align==0
            records.append(dict(main=main,sub=sub,offset=offset,bytes=length,kind=kind))
        for r in records:
            f.seek(r['offset']);h=hashlib.sha256();h1=hashlib.sha1();left=r['bytes']
            while left:
                data=f.read(min(left,4*1024**2));assert data;left-=len(data);h.update(data);h1.update(data)
            r['sha256']=h.hexdigest()
            r['sha1']=h1.hexdigest()
            if r['main']=='VERIFY':continue
            name='DDR.USB' if (r['main']=='USB' or r['sub']=='bootloader') else ('_aml_dtb.PARTITION' if r['main']=='dtb' else ('platform.conf' if r['main']=='conf' else r['sub']+'.PARTITION'))
            assert r['sha256']==hash_file(payloads/name),name
        for r in records:
            if r['main']!='VERIFY':continue
            part=next(p for p in records if p['main']=='PARTITION' and p['sub']==r['sub'])
            f.seek(r['offset'])
            assert f.read(r['bytes'])==('sha1sum '+part['sha1']).encode(),r['sub']
    for part,raw in [('system','bootfs.raw'),('data','rootfs.raw')]:
        assert sparse_hash(payloads/(part+'.PARTITION'))==hash_file(work/raw)
    script_report = verify_fat(work / 'bootfs.raw')
    (work/'checks/boot-script.json').write_text(json.dumps(script_report, indent=2))
    boot=(payloads/'boot.PARTITION').read_bytes()
    ksize,_,rsize=struct.unpack_from('<III',boot,8);page=struct.unpack_from('<I',boot,36)[0]
    kernel=boot[page:page+ksize];off=page+((ksize+page-1)//page)*page
    ramdisk=boot[off:off+rsize]
    h=hashlib.sha1()
    for part in [kernel,ramdisk,b'']:h.update(part);h.update(struct.pack('<I',len(part)))
    assert boot[576:596]==h.digest()
    entries=cpio_files(gzip.decompress(ramdisk))
    assert entries['init']==(work/'bootstrap/init').read_bytes()
    assert set(entries)=={'dev','proc','sys','dev/console','dev/null','init'}
    logo=(payloads/'logo.PARTITION').read_bytes()
    assert logo[8:16]==b'AML_RES!' and struct.unpack_from('<I',logo,4)[0]==2
    assert struct.unpack_from('<I',logo,20)[0]==1 and logo[96:128].split(b'\0')[0]==b'bootup'
    length,start=struct.unpack_from('<II',logo,72)
    assert logo[start:start+length]==a.logo.read_bytes()
    report=dict(image=img.name,bytes=img.stat().st_size,sha256=hash_file(img),offline_checks_passed=True,board_flashed=False,runtime_release='6.18.49-ophub',items=records)
    (work/'checks/final-package.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='items'}))

if __name__=='__main__':main()
