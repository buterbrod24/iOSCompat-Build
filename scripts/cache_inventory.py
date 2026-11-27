#!/usr/bin/env python3
"""Read-only inventory of dyld cache header, mappings and image paths, not exports."""
import argparse, json, os, struct, uuid
from pathlib import Path

def read_at(f, size, offset, count):
    if offset<0 or count<0 or offset+count>size:
        raise ValueError("range outside cache file")
    f.seek(offset)
    data=f.read(count)
    if len(data)!=count:
        raise ValueError("truncated cache read")
    return data

def inspect(f):
    size=f.seek(0,os.SEEK_END)
    header=read_at(f,size,0,min(size,456))
    if len(header)<104 or not header.startswith(b"dyld_v1"):
        raise ValueError("unsupported dyld cache header")
    magic=header[:16].rstrip(b"\0 ").decode("ascii")
    arch=magic.split()[-1]
    if arch not in ("arm64","arm64e"):
        raise ValueError("unsupported cache architecture")
    mo,mc,oldoff,oldcount=struct.unpack_from("<4I",header,16)
    if not 104<=mo<=size or not 1<=mc<=4096:
        raise ValueError("invalid mapping table")
    def field(off,fmt):
        n=struct.calcsize(fmt)
        if off+n>min(mo,len(header)):
            return None
        return struct.unpack_from(fmt,header,off)
    mappings=[]
    table=read_at(f,size,mo,mc*32)
    for address,length,offset,maxprot,initprot in struct.iter_unpack("<QQQII",table):
        if not length or offset+length>size or address+length>1<<64:
            raise ValueError("invalid cache mapping extent")
        mappings.append(dict(address=address,size=length,file_offset=offset,max_prot=maxprot,init_prot=initprot))
    by_vm=sorted(mappings,key=lambda m:m["address"])
    for a,b in zip(by_vm,by_vm[1:]):
        if a["address"]+a["size"]>b["address"]:
            raise ValueError("overlapping VM mappings")
    modern=field(448,"<II")
    io,ic=modern if modern is not None else (oldoff,oldcount)
    if ic>100000 or (ic and io<mo):
        raise ValueError("invalid image table")
    images=[]
    if ic:
        for address,_,_,pathoff,_ in struct.iter_unpack("<QQQII",read_at(f,size,io,ic*32)):
            if not 0<pathoff<size:
                raise ValueError("invalid image path offset")
            raw=read_at(f,size,pathoff,min(4096,size-pathoff))
            end=raw.find(b"\0")
            if end<0: raise ValueError("unterminated image path")
            path=raw[:end].decode("utf-8")
            if not path.startswith("/"): raise ValueError("invalid image path")
            local=[m for m in mappings if m["address"]<=address<m["address"]+m["size"]]
            images.append({"path":path,"address":address,
                           "local_mapping":bool(local)})
    osver=field(364,"<I")
    platform=field(216,"<I")
    subs=field(392,"<II")
    subcount=subs[1] if subs else None
    if subcount is not None and subcount>4096:
        raise ValueError("subcache count exceeds budget")
    if subcount and (subs[0]<mo or subs[0]+subcount*24>size):
        raise ValueError("subcache array outside file")
    return {"architecture":arch,"uuid":str(uuid.UUID(bytes=header[88:104])),
            "platform":platform[0] if platform else None,
            "os_version":([osver[0]>>16,(osver[0]>>8)&255,osver[0]&255] if osver and osver[0] else None),
            "declared_subcache_count":subcount,"image_table":"modern" if modern is not None else "legacy",
            "mappings":mappings,"images":images,
            "scope":"Single supplied cache file metadata; subcache identity, exports and runtime resolution unverified"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("cache",type=Path)
    p.add_argument("--match",default="",help="Case-sensitive image path substring")
    a=p.parse_args()
    with a.cache.open("rb") as f: r=inspect(f)
    r["image_count"]=len(r["images"])
    if a.match: r["images"]=[x for x in r["images"] if a.match in x["path"]]
    print(json.dumps(r,indent=2))
if __name__=="__main__":
    main()
