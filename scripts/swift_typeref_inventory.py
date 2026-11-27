#!/usr/bin/env python3
"""Bounded framing of Swift compiler-emitted symbolic name bytes; never resolve pointers."""
import argparse,json,struct
from collections import Counter
from pathlib import Path

MAX_SECTION=32*1024*1024
MAX_NAMES=500000

def scan(data):
    """Scan a supplied 64-bit __swift5_typeref section, without interpreting payloads.

    Zero bytes outside a reference end a name or act as padding.
    Unknown control-byte kinds still have a documented framing width;
    their meanings and target addresses are intentionally not decoded.
    """
    if len(data)>MAX_SECTION:
        raise ValueError("section exceeds limit")
    i=0
    names=0
    refs=Counter()
    with_refs=0
    while i<len(data):
        if data[i]==0:
            i+=1
            continue
        found=False
        content=False
        while i<len(data) and data[i]!=0:
            byte=data[i]
            if 1<=byte<=31:
                width=4 if byte<=23 else 8
                if i+1+width>len(data):
                    raise ValueError("truncated symbolic reference")
                refs[f"0x{byte:02x}"]+=1
                found=True
                content=True
                i+=1+width
            elif byte==255:
                i+=1
            elif 32<=byte<=126 or byte>=128:
                content=True
                i+=1
            else:
                raise ValueError("unexpected byte in symbolic name")
        if i==len(data):
            raise ValueError("missing name terminator")
        i+=1
        if content:
            names+=1
            with_refs+=int(found)
        if names>MAX_NAMES:
            raise ValueError("name count exceeds limit")
    return {"records":names,"records_with_references":with_refs,
            "reference_markers":dict(sorted(refs.items())),
            "scope":"Byte framing only; section may contain padding or shared strings. No pointer resolution, target validation, or mangling grammar verification."}

def section(data):
    """Find one file-backed ARM64 Mach-O __swift5_typeref section."""
    if len(data)<32:
        raise ValueError("truncated Mach-O")
    magic,cpu,sub,filetype,ncmds,sizeofcmds,flags,reserved=struct.unpack_from("<8I",data)
    if magic!=0xfeedfacf or cpu!=0x100000c:
        raise ValueError("requires thin little-endian ARM64 Mach-O")
    if ncmds>32768 or sizeofcmds>len(data)-32:
        raise ValueError("load command bounds")
    end=32+sizeofcmds
    off=32
    matches=[]
    for _ in range(ncmds):
        if off+8>end:
            raise ValueError("truncated load command")
        cmd,size=struct.unpack_from("<II",data,off)
        if size<8 or size%8 or off+size>end:
            raise ValueError("invalid load command size")
        if cmd==0x19:
            if size<72:
                raise ValueError("truncated segment")
            nsects=struct.unpack_from("<I",data,off+64)[0]
            if nsects>(size-72)//80:
                raise ValueError("invalid section count")
            for j in range(nsects):
                p=off+72+80*j
                name=data[p:p+16].split(b"\0",1)[0]
                seg=data[p+16:p+32].split(b"\0",1)[0]
                if name!=b"__swift5_typeref":
                    continue
                addr,length,offset=struct.unpack_from("<QQI",data,p+32)
                section_flags=struct.unpack_from("<I",data,p+64)[0]
                if seg!=b"__TEXT" or section_flags&0xff in (1,12,18):
                    raise ValueError("unsupported type reference section")
                if length>MAX_SECTION or offset>len(data) or offset<end or length>len(data)-offset:
                    raise ValueError("section out of bounds")
                matches.append((offset,length))
        off+=size
    if off!=end or len(matches)>1:
        raise ValueError("ambiguous section or command size")
    if not matches:
        return None
    start,length=matches[0]
    return data[start:start+length]

def inspect(data):
    payload=section(data)
    if payload is None:
        return {"status":"section_not_observed"}
    return {"status":"framed","bytes":len(payload),**scan(payload)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    a=p.parse_args()
    if a.image.stat().st_size>256*1024*1024:
        p.error("image exceeds input limit")
    print(json.dumps(inspect(a.image.read_bytes()),indent=2))
if __name__=="__main__":
    main()
