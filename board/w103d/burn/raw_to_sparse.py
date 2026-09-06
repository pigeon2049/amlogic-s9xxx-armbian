#!/usr/bin/env python3
"""Encode Android sparse v1, using RAW and explicit zero FILL chunks."""
import argparse,hashlib,json,pathlib,struct,zlib

def convert(source,target):
    size=source.stat().st_size
    assert size%4096==0
    chunks=0;checksum=0;raw_sha=hashlib.sha256();zero=bytes(1024**2)
    with source.open('rb') as src,target.open('wb+') as dst:
        dst.write(bytes(28))
        while data:=src.read(len(zero)):
            blocks=len(data)//4096
            checksum=zlib.crc32(data,checksum);raw_sha.update(data)
            if data==zero[:len(data)]:dst.write(struct.pack('<HHIII',0xcac2,0,blocks,16,0))
            else:dst.write(struct.pack('<HHII',0xcac1,0,blocks,12+len(data)));dst.write(data)
            chunks+=1
        dst.seek(0);dst.write(struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,4096,size//4096,chunks,checksum))
    info=dict(raw_bytes=size,raw_sha256=raw_sha.hexdigest(),sparse_bytes=target.stat().st_size,chunks=chunks,crc32=f'{checksum:08x}')
    target.with_suffix('.sparse.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('target',type=pathlib.Path);a=p.parse_args();convert(a.source,a.target)
