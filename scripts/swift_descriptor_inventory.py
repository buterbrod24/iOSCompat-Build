#!/usr/bin/env python3
"""Read direct Swift nominal type descriptor headers from standalone ARM64 Mach-O."""
import argparse,json,struct
from collections import Counter
from pathlib import Path
from swift_generic_context import inspect_generic

KINDS={16:"class",17:"struct",18:"enum"}
MAX_IMAGE=256*1024*1024
MAX_RECORDS=500000

def inspect(data):
    if len(data)<32 or len(data)>MAX_IMAGE:
        raise ValueError("image size")
    magic,cpu,sub,ft,ncmds,sz,flags,res=struct.unpack_from("<8I",data)
    if magic!=0xfeedfacf or cpu!=0x100000c or ft not in (2,6,8):
        raise ValueError("requires standalone ARM64 executable, dylib or bundle")
    if ncmds>32768 or sz>len(data)-32:
        raise ValueError("command bounds")
    end=32+sz
    off=32
    text=[]
    tables=[]
    for _ in range(ncmds):
        if off+8>end: raise ValueError("truncated command")
        cmd,size=struct.unpack_from("<II",data,off)
        if size<8 or size%8 or off+size>end: raise ValueError("invalid command size")
        if cmd==0x19:
            if size<72: raise ValueError("truncated segment")
            seg=data[off+8:off+24].split(b"\0",1)[0]
            vm,vs,fo,fs,mp,ip,ns,sflags=struct.unpack_from("<QQQQIIII",data,off+24)
            if ns>(size-72)//80 or fs>vs or fo>len(data) or fs>len(data)-fo or vm+vs>2**64:
                raise ValueError("invalid segment bounds")
            if seg==b"__TEXT" and ip&1 and not ip&2 and fs:
                text.append((vm,fs,fo))
            for j in range(ns):
                p=off+72+80*j
                name=data[p:p+16].split(b"\0",1)[0]
                sseg=data[p+16:p+32].split(b"\0",1)[0]
                if name!=b"__swift5_types": continue
                addr,length,offset=struct.unpack_from("<QQI",data,p+32)
                sf=struct.unpack_from("<I",data,p+64)[0]
                if seg!=b"__TEXT" or sseg!=seg or not ip&1 or ip&2 or sf&255 in (1,12,18):
                    raise ValueError("unsupported type table")
                if length%4 or length//4>MAX_RECORDS or addr%4 or offset<end or addr<vm or addr-vm>fs or length>fs-(addr-vm) or offset!=fo+addr-vm:
                    raise ValueError("type table bounds")
                tables.append((addr,length,offset))
        off+=size
    if off!=end or len(tables)>1 or len(text)>1:
        raise ValueError("ambiguous command or section")
    if not tables: return {"status":"section_not_observed"}
    if not text: raise ValueError("missing readonly __TEXT")
    vm,fs,fo=text[0]
    addr,length,start=tables[0]
    status=Counter()
    kinds=Counter()
    versions=Counter()
    generic=0
    unique=0
    seen=set()
    generic_values=[]
    generic_classes=0
    generic_budget=10000
    for i in range(0,length,4):
        raw=struct.unpack_from("<i",data,start+i)[0]
        tag=raw&3
        if tag!=0:
            status["indirect_unresolved" if tag==1 else "unsupported_reference_kind"]+=1
            continue
        target=addr+i+(raw&~3)
        if raw==0 or target<vm or target-vm>fs-8 or target%4 or addr<=target<addr+length:
            status["direct_outside_supported_range"]+=1
            continue
        pos=fo+target-vm
        if pos<end:
            status["direct_outside_supported_range"]+=1
            continue
        word=struct.unpack_from("<I",data,pos)[0]
        kind=word&31
        if kind not in KINDS:
            status["unexpected_descriptor_kind"]+=1
            continue
        version=(word>>8)&255
        if version!=0:
            status["unsupported_descriptor_version"]+=1
            continue
        # Nominal descriptors have a common 20-byte prefix in Swift 5.9.
        if target-vm>fs-20:
            status["truncated_nominal_prefix"]+=1
            continue
        if target in seen:
            status["duplicate_direct_reference"]+=1
            continue
        seen.add(target)
        status["direct_nominal_header"]+=1
        kinds[KINDS[kind]]+=1
        versions[str(version)]+=1
        generic+=bool(word&128)
        unique+=bool(word&64)
        if word&128:
            if kind==16:
                generic_classes+=1
            elif len(generic_values)<generic_budget:
                generic_values.append(pos)
    # Bound arrays to readonly file-backed text and the next observed nominal
    # descriptor or table start. This is not a proof of descriptor extent.
    from bisect import bisect_right
    bounds=sorted({fo+t-vm for t in seen}|{start,fo+fs})
    contexts=[]
    for pos in generic_values:
        end_pos=bounds[bisect_right(bounds,pos)]
        contexts.append(inspect_generic(data,pos,end_pos))
    context_status=Counter(x["status"] for x in contexts)
    return {"status":"inspected","architecture_subtype":sub&0xffffff,
            "records":length//4,"record_status":dict(sorted(status.items())),
            "nominal_kinds":dict(sorted(kinds.items())),"versions":dict(sorted(versions.items())),
            "generic_headers":generic,"unique_flag_headers":unique,
            "generic_value_contexts":{"observed":len(contexts),"skipped_budget":generic-generic_classes-len(contexts),
              "classes_not_parsed":generic_classes,"status_counts":dict(sorted(context_status.items())),
              "nonzero_legacy_extra_field":sum(x.get("nonzero_legacy_extra_field",False) for x in contexts),
              "type_pack_flag":sum(x.get("type_pack_flag",False) for x in contexts),
              "details":contexts},
            "scope":"Direct relative file-offset headers in read-only __TEXT only. Generic value-type fixed arrays bounded by observed neighbors; not validated full descriptor extents. No indirect reference resolution, parent traversal, metadata access calls, authentication or layout validation."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    a=p.parse_args()
    if a.image.stat().st_size>MAX_IMAGE:p.error("image too large")
    print(json.dumps(inspect(a.image.read_bytes()),indent=2))
if __name__=="__main__":
    main()
