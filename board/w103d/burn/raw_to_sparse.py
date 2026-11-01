#!/usr/bin/env python3
"""Encode Android sparse v1, using RAW and explicit zero FILL chunks.

Zero runs are detected per 4 KiB block (not per 1 MiB window), so partly
used megabytes no longer carry their zero blocks as RAW data."""
import argparse,hashlib,json,pathlib,struct,zlib

def convert(source,target):
    size=source.stat().st_size
    assert size%4096==0
    chunks=0;checksum=0;raw_sha=hashlib.sha256();zero=bytes(4096)
    run_zero=None;run=[]
    def flush():
        nonlocal chunks
        if not run:return
        if run_zero:dst.write(struct.pack('<HHIII',0xcac2,0,len(run),16,0))
        else:raw=b''.join(run);dst.write(struct.pack('<HHII',0xcac1,0,len(run),12+len(raw)));dst.write(raw)
        chunks+=1;run.clear()
    with source.open('rb') as src,target.open('wb+') as dst:
        dst.write(bytes(28))
        while data:=src.read(1024**2):
            checksum=zlib.crc32(data,checksum);raw_sha.update(data)
            for i in range(0,len(data),4096):
                block=data[i:i+4096];is_zero=block==zero
                if is_zero!=run_zero or len(run)>=8192:flush();run_zero=is_zero
                run.append(None if is_zero else block)
        flush()
        dst.seek(0);dst.write(struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,4096,size//4096,chunks,checksum))
    info=dict(raw_bytes=size,raw_sha256=raw_sha.hexdigest(),sparse_bytes=target.stat().st_size,chunks=chunks,crc32=f'{checksum:08x}')
    target.with_suffix('.sparse.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('target',type=pathlib.Path);a=p.parse_args();convert(a.source,a.target)
