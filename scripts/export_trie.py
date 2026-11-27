#!/usr/bin/env python3
"""Read-only export trie evidence for standalone thin Mach-O images, not shared caches."""
import struct
from macho_imports import read_dependencies

def uleb(data,pos,end):
    value=0
    for shift in range(0,70,7):
        if pos>=end:
            raise ValueError("truncated ULEB128")
        b=data[pos]
        pos+=1
        if shift==63 and b>1:
            raise ValueError("ULEB128 overflow")
        value|=(b&127)<<shift
        if not b&128:
            return value,pos
    raise ValueError("ULEB128 overflow")

def cstring(data,pos,end):
    stop=data.find(b"\0",pos,end)
    if stop<0:
        raise ValueError("unterminated export string")
    if stop-pos>8192:
        raise ValueError("export string too long")
    return data[pos:stop],stop+1

def decode_trie(data,deps):
    if not data:
        return {}
    if len(data)>32*1024*1024:
        raise ValueError("export trie exceeds budget")
    entries={}
    stack=[(0,b"",())]
    visited=0
    while stack:
        off,prefix,ancestors=stack.pop()
        visited+=1
        if visited>500000 or len(ancestors)>256 or len(prefix)>8192:
            raise ValueError("export trie traversal exceeds budget")
        if off in ancestors or off>=len(data):
            raise ValueError("invalid or cyclic export trie")
        size,pos=uleb(data,off,len(data))
        end=pos+size
        if end>=len(data):
            raise ValueError("export terminal outside trie")
        if size:
            flags,pos=uleb(data,pos,end)
            if flags&~0x1f or flags&3==3:
                raise ValueError("unsupported export flags")
            if not prefix or prefix in entries:
                raise ValueError("empty or duplicate export name")
            row={"flags":flags,"weak_definition":bool(flags&4)}
            if flags&8:
                if flags&0x13:
                    raise ValueError("unsupported reexport flag combination")
                ordinal,pos=uleb(data,pos,end)
                renamed,pos=cstring(data,pos,end)
                if not 1<=ordinal<=len(deps):
                    raise ValueError("invalid reexport ordinal")
                row.update(kind="reexport",provider=deps[ordinal-1]["path"],
                           import_name=(renamed or prefix).decode("utf-8","strict"))
            else:
                _,pos=uleb(data,pos,end)
                kind={0:"regular",1:"thread_local",2:"absolute"}[flags&3]
                if flags&16:
                    if kind!="regular":
                        raise ValueError("unsupported resolver kind")
                    _,pos=uleb(data,pos,end)
                    kind="stub_resolver"
                row.update(kind=kind)
            if pos!=end:
                raise ValueError("unexpected terminal payload")
            entries[prefix.decode("utf-8","strict")]=row
        children=data[end]
        pos=end+1
        labels=set()
        for _ in range(children):
            label,pos=cstring(data,pos,len(data))
            child,pos=uleb(data,pos,len(data))
            if not label or label in labels or child>=len(data):
                raise ValueError("invalid export child")
            labels.add(label)
            stack.append((child,prefix+label,ancestors+(off,)))
        if len(stack)>500000:
            raise ValueError("export trie pending traversal exceeds budget")
    return entries

def inspect_exports(data):
    deps,_=read_dependencies(data)
    ncmd,size=struct.unpack_from("<II",data,16)
    pos=32
    locations=[]
    commands=[]
    for _ in range(ncmd):
        cmd,length=struct.unpack_from("<II",data,pos)
        if cmd==0x80000033:
            if length!=16:
                raise ValueError("invalid exports trie command")
            off,count=struct.unpack_from("<II",data,pos+8)
            commands.append("LC_DYLD_EXPORTS_TRIE")
            if count:
                locations.append((off,count))
        elif cmd in (0x22,0x80000022):
            if length!=48:
                raise ValueError("invalid dyld info command")
            off,count=struct.unpack_from("<II",data,pos+40)
            commands.append("LC_DYLD_INFO")
            if count:
                locations.append((off,count))
        pos+=length
    reexports=[dep["path"] for dep in deps if dep["kind"]=="reexport"]
    base={"scope":"Standalone image export trie; no shared-cache, legacy symbol-table or runtime resolution claim",
          "commands":commands,"reexport_libraries":reexports}
    if not locations:
        return dict(base,status="trie_not_available",symbols={})
    if len(set(locations))!=1:
        raise ValueError("conflicting export trie locations")
    off,count=locations[0]
    if off<32+size or off+count>len(data) or count>32*1024*1024:
        raise ValueError("export trie outside supported bounds")
    return dict(base,status="trie_inspected",symbols=decode_trie(data[off:off+count],deps))

def summarize_exports(result):
    from collections import Counter
    return {k:v for k,v in result.items() if k!="symbols"} | {
        "entry_counts":dict(Counter(v["kind"] for v in result["symbols"].values()))}

def main():
    import argparse,json,pathlib
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=pathlib.Path)
    p.add_argument("--symbol",action="append",default=[])
    args=p.parse_args()
    if args.image.stat().st_size>256*1024*1024:
        p.error("image exceeds input budget")
    result=inspect_exports(args.image.read_bytes())
    summary=summarize_exports(result)
    summary["queries"]={name:result["symbols"].get(name,{"kind":"not_observed"}) for name in args.symbol}
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    main()
