#!/usr/bin/env python3
"""Read-only export names from supplied, metadata-matched dyld cache parts."""
import argparse, bisect, json, struct
from contextlib import ExitStack
from pathlib import Path
from cache_inventory import inspect, read_at
from cache_set import declarations, verify
from macho_imports import read_dependencies
from export_trie import decode_trie, summarize_exports

class VMReader:
    def __init__(self, ranges, files):
        self.ranges=sorted(ranges,key=lambda m:m["address"])
        self.starts=[m["address"] for m in self.ranges]
        self.files=files
        for a,b in zip(self.ranges,self.ranges[1:]):
            if a["address"]+a["size"]>b["address"]:
                raise ValueError("ambiguous VM mappings")

    def read(self,address,count):
        if address<0 or count<0 or count>32*1024*1024 or address+count>1<<64:
            raise ValueError("invalid or oversized VM read")
        if not count: return b""
        i=bisect.bisect_right(self.starts,address)-1
        if i<0: raise ValueError("unmapped VM address")
        m=self.ranges[i]
        delta=address-m["address"]
        if delta+count>m["size"]:
            raise ValueError("VM read crosses mapping boundary")
        f,size=self.files[m["cache_uuid"]]
        return read_at(f,size,m["file_offset"]+delta,count)

def inspect_image(reader,address):
    header=reader.read(address,32)
    magic,cpu,subtype,kind,ncmd,size,flags,_=struct.unpack("<8I",header)
    if magic!=0xfeedfacf or cpu!=0x100000c or kind!=6:
        raise ValueError("unsupported cached image header")
    if ncmd>65536 or size>4*1024*1024 or ncmd>size//8:
        raise ValueError("invalid cached load command table")
    commands=reader.read(address,32+size)
    deps,_=read_dependencies(commands)
    pos=32
    linkedit=[]
    text=[]
    locations=[]
    names=[]
    for _ in range(ncmd):
        cmd,length=struct.unpack_from("<II",commands,pos)
        if cmd==0x19:
            if length<72: raise ValueError("short segment command")
            name=commands[pos+8:pos+24].split(b"\0",1)[0]
            vm,vmsize,off,filesize=struct.unpack_from("<4Q",commands,pos+24)
            if name==b"__LINKEDIT": linkedit.append((vm,vmsize,off,filesize))
            if name==b"__TEXT": text.append((vm,vmsize))
        elif cmd==0xd:
            if length<24: raise ValueError("short install name command")
            off=struct.unpack_from("<I",commands,pos+8)[0]
            if not 24<=off<length: raise ValueError("invalid install name")
            end=commands.find(b"\0",pos+off,pos+length)
            if end<0: raise ValueError("unterminated install name")
            names.append(commands[pos+off:end].decode("utf-8"))
        elif cmd==0x80000033:
            if length!=16: raise ValueError("invalid export trie command")
            off,count=struct.unpack_from("<II",commands,pos+8)
            if count: locations.append((off,count))
        elif cmd in (0x22,0x80000022):
            if length!=48: raise ValueError("invalid dyld info command")
            off,count=struct.unpack_from("<II",commands,pos+40)
            if count: locations.append((off,count))
        pos+=length
    if len(text)!=1 or text[0][0]!=address or 32+size>text[0][1] or len(names)!=1:
        raise ValueError("image header and segment identity unverified")
    base={"install_name":names[0],"architecture":[cpu,subtype],
          "reexport_libraries":[d["path"] for d in deps if d["kind"]=="reexport"],
          "scope":"Cache export metadata only, not runtime binding or ABI evidence"}
    if not locations:
        return dict(base,status="trie_not_available",symbols={})
    if len(set(locations))!=1 or len(linkedit)!=1:
        raise ValueError("ambiguous export trie or LINKEDIT")
    off,count=locations[0]
    vm,vmsize,fileoff,filesize=linkedit[0]
    delta=off-fileoff
    if delta<0 or delta+count>min(vmsize,filesize) or count>32*1024*1024:
        raise ValueError("export trie outside LINKEDIT")
    data=reader.read(vm+delta,count)
    return dict(base,status="trie_inspected",symbols=decode_trie(data,deps))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider",required=True)
    p.add_argument("--symbol",action="append",default=[])
    p.add_argument("main",type=Path)
    p.add_argument("parts",type=Path,nargs="*")
    a=p.parse_args()
    with ExitStack() as stack:
        f=stack.enter_context(a.main.open("rb"))
        root=inspect(f)
        expected=declarations(f)
        files={root["uuid"]:(f,f.seek(0,2))}
        parts=[]
        for path in a.parts:
            handle=stack.enter_context(path.open("rb"))
            r=inspect(handle)
            parts.append(r)
            if r["uuid"] in files: raise ValueError("duplicate cache UUID")
            files[r["uuid"]]=(handle,handle.seek(0,2))
        matched=verify(root,expected,parts)
        if matched["status"]!="declared_parts_matched":
            raise ValueError("cache set incomplete or unverified")
        images=[x for x in root["images"] if x["path"]==a.provider]
        if len(images)!=1:
            raise ValueError("provider path not uniquely indexed")
        result=inspect_image(VMReader(matched["mappings"],files),images[0]["address"])
        summary=summarize_exports(result)
        summary.update(cache_uuid=root["uuid"],cache_architecture=root["architecture"],
                       cache_os_version=root["os_version"],indexed_path=a.provider,
                       install_name_matches=result["install_name"]==a.provider,
                       queries={name:result["symbols"].get(name,{"kind":"not_observed"}) for name in a.symbol})
        print(json.dumps(summary,indent=2))
if __name__=="__main__":
    main()
