#!/usr/bin/env python3
"""Conservative reexport path evidence in a supplied set of standalone Mach-O images."""
import argparse,json,pathlib,struct
from export_trie import inspect_exports

def install_name(data):
    ncmd,size=struct.unpack_from("<II",data,16)
    pos=32
    names=[]
    for _ in range(ncmd):
        cmd,length=struct.unpack_from("<II",data,pos)
        if cmd==0xd:
            if length<24: raise ValueError("short LC_ID_DYLIB")
            offset=struct.unpack_from("<I",data,pos+8)[0]
            if not 24<=offset<length: raise ValueError("invalid install name offset")
            end=data.find(b"\0",pos+offset,pos+length)
            if end<0: raise ValueError("unterminated install name")
            names.append(data[pos+offset:end].decode("utf-8"))
        pos+=length
    if len(names)!=1: raise ValueError("expected exactly one install name")
    return names[0]

def load_images(paths):
    images={}
    budget=512*1024*1024
    for path in paths:
        size=path.stat().st_size
        if size>min(budget,256*1024*1024): raise ValueError("image budget exceeded")
        budget-=size
        data=path.read_bytes()
        record=inspect_exports(data)
        name=install_name(data)
        if name in images: raise ValueError("ambiguous install name: "+name)
        cpu,subtype=struct.unpack_from("<II",data,4)
        images[name]=dict(record,architecture=[cpu,subtype])
    return images

def trace(images,provider,symbol):
    paths=[]
    blockers=[]
    pending=[(provider,symbol,())]
    visits=0
    architecture=images.get(provider,{}).get("architecture")
    while pending:
        lib,name,chain=pending.pop()
        visits+=1
        if visits>4096:
            blockers.append("traversal budget exceeded")
            break
        node=(lib,name)
        if node in chain or len(chain)>=64:
            blockers.append("cycle or depth limit at "+lib+" "+name)
            continue
        chain=chain+(node,)
        record=images.get(lib)
        if record is None:
            blockers.append("image not supplied: "+lib)
            continue
        if record.get("architecture")!=architecture:
            blockers.append("architecture mismatch: "+lib)
            continue
        if record.get("status")!="trie_inspected":
            blockers.append("export trie not inspected: "+lib)
            continue
        entry=record["symbols"].get(name)
        if entry:
            if entry["kind"]=="reexport":
                pending.append((entry["provider"],entry["import_name"],chain))
            else:
                paths.append({"chain":[{"provider":p,"symbol":s} for p,s in chain],
                              "terminal_kind":entry["kind"],"weak_definition":entry["weak_definition"]})
            # Explicit terminal takes precedence over exploring generic reexports
            # in this evidence model; no actual dyld ordering claim.
            continue
        for other in reversed(record.get("reexport_libraries",[])):
            pending.append((other,name,chain))
    return {"status":"candidate_path_found" if paths else "not_observed",
            "paths":paths,"blockers":sorted(set(blockers)),
            "scope":"Exact install-name graph of supplied files only; not dyld path resolution, ABI or system absence proof"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider",required=True)
    p.add_argument("--symbol",required=True)
    p.add_argument("images",type=pathlib.Path,nargs="+")
    a=p.parse_args()
    print(json.dumps(trace(load_images(a.images),a.provider,a.symbol),indent=2))
if __name__=="__main__":
    main()
