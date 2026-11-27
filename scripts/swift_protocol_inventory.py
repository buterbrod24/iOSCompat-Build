#!/usr/bin/env python3
"""Read fixed Swift protocol and conformance headers from standalone ARM64 Mach-O."""
import argparse,json,struct
from collections import Counter
from pathlib import Path
from bisect import bisect_right
from swift_witness_control import inspect_witness_control

MAX_IMAGE=256*1024*1024
MAX_RECORDS=500000
TABLES={b"__swift5_protos":"protocols",b"__swift5_proto":"conformances"}

def inspect(data):
    if not 32<=len(data)<=MAX_IMAGE: raise ValueError("image size")
    magic,cpu,sub,ft,ncmds,sz,flags,res=struct.unpack_from("<8I",data)
    if magic!=0xfeedfacf or cpu!=0x100000c or ft not in (2,6,8):
        raise ValueError("requires standalone ARM64 Mach-O")
    if ncmds>32768 or sz>len(data)-32: raise ValueError("command bounds")
    end=32+sz
    off=32
    text=[]
    tables={}
    for _ in range(ncmds):
        if off+8>end: raise ValueError("truncated command")
        cmd,size=struct.unpack_from("<II",data,off)
        if size<8 or size%8 or off+size>end: raise ValueError("invalid command size")
        if cmd==0x19:
            if size<72: raise ValueError("truncated segment")
            seg=data[off+8:off+24].split(b"\0",1)[0]
            vm,vs,fo,fs,mp,ip,ns,sflags=struct.unpack_from("<QQQQIIII",data,off+24)
            if ns>(size-72)//80 or fs>vs or fo>len(data) or fs>len(data)-fo or vm+vs>2**64:
                raise ValueError("segment bounds")
            if seg==b"__TEXT" and ip&1 and not ip&2 and fs: text.append((vm,fs,fo))
            for j in range(ns):
                p=off+72+80*j
                name=data[p:p+16].split(b"\0",1)[0]
                if name not in TABLES: continue
                key=TABLES[name]
                sseg=data[p+16:p+32].split(b"\0",1)[0]
                addr,length,offset=struct.unpack_from("<QQI",data,p+32)
                sf=struct.unpack_from("<I",data,p+64)[0]
                if key in tables or seg!=b"__TEXT" or sseg!=seg or not ip&1 or ip&2 or (sf&255) in (1,12,18):
                    raise ValueError("unsupported or duplicate table")
                if length%4 or length//4>MAX_RECORDS or addr%4 or offset<end or addr<vm or addr-vm>fs or length>fs-(addr-vm) or offset!=fo+addr-vm:
                    raise ValueError("table bounds")
                tables[key]=(addr,length,offset)
        off+=size
    if off!=end or len(text)>1: raise ValueError("ambiguous command or segment")
    if not tables: return {"status":"sections_not_observed"}
    if not text: raise ValueError("missing readonly __TEXT")
    vm,fs,fo=text[0]
    intervals=sorted((a,a+l) for a,l,_ in tables.values() if l)
    if any(b>c for (_,b),(c,_) in zip(intervals,intervals[1:])):
        raise ValueError("overlapping tables")
    # Neighboring record targets supply conservative bounds, not proven extents.
    bounds={fo+fs}
    for a,l,o in tables.values():
        bounds.add(o)
        for i in range(0,l,4):
            raw=struct.unpack_from("<i",data,o+i)[0]
            target=a+i+raw
            if raw and not raw&3 and vm<=target<vm+fs:
                bounds.add(fo+target-vm)
    bounds=sorted(bounds)
    result={"status":"inspected","architecture_subtype":sub&0xffffff}
    for key in ("protocols","conformances"):
        if key not in tables:
            result[key]={"status":"section_not_observed"};continue
        addr,length,start=tables[key]
        states=Counter()
        kinds=Counter()
        flags_count=Counter()
        requirement_counts=Counter()
        seen=set()
        witness_states=Counter()
        generic_controls=0
        template_words=Counter()
        resilient_records=0
        for i in range(0,length,4):
            raw=struct.unpack_from("<i",data,start+i)[0]
            # Protocol record uses a tagged relative context pointer. Only zero
            # tag is examined. Conformance record uses an untagged direct offset.
            if raw&3:
                states["tagged_or_unaligned_unresolved"]+=1;continue
            target=addr+i+raw
            prefix=24 if key=="protocols" else 16
            if raw==0 or target<vm or target-vm>fs-prefix or target%4 or fo+target-vm<end or any(target<b and target+prefix>a for a,b in intervals):
                states["outside_supported_range"]+=1;continue
            if target in seen:
                states["duplicate_reference"]+=1;continue
            pos=fo+target-vm
            if key=="protocols":
                word,parent,name,signature,requirements,associated=struct.unpack_from("<6I",data,pos)
                if word&31!=3 or (word>>8)&255:
                    states["unsupported_protocol_header"]+=1;continue
                requirement_counts["signature_requirements"]+=signature
                requirement_counts["protocol_requirements"]+=requirements
            else:
                proto,typ,witness,word=struct.unpack_from("<4I",data,pos)
                type_kind=(word>>3)&7
                # Unknown/reserved flags are not treated as recognized headers.
                if type_kind>3 or word&0x00fc0007:
                    states["unsupported_conformance_flags"]+=1;continue
                kinds[str(type_kind)]+=1
                flags_count["retroactive"]+=bool(word&64)
                flags_count["synthesized_nonunique"]+=bool(word&128)
                flags_count["resilient_witnesses"]+=bool(word&65536)
                flags_count["generic_witness_table"]+=bool(word&131072)
                requirement_counts["conditional_requirements"]+=(word>>8)&255
                requirement_counts["conditional_pack_descriptors"]+=(word>>24)&255
                if word&(65536|131072):
                    control=inspect_witness_control(data,pos,bounds[bisect_right(bounds,pos)],word)
                    witness_states[control["status"]]+=1
                    if control["status"]=="trailing_headers_observed":
                        resilient_records+=control.get("resilient_witness_records",0)
                        if "generic_witness_control" in control:
                            generic_controls+=1
                            template_words[str(control["generic_witness_control"]["template_words"])]+=1
            seen.add(target)
            states["fixed_header_observed"]+=1
        result[key]={"records":length//4,"record_status":dict(sorted(states.items())),
                     "type_reference_kinds":dict(sorted(kinds.items())),
                     "flags":dict(sorted(flags_count.items())),
                     "requirement_counts":dict(sorted(requirement_counts.items()))}
        if key=="conformances":
            result[key]["witness_controls"]={"status_counts":dict(sorted(witness_states.items())),
                "generic_controls_observed":generic_controls,
                "template_word_histogram":dict(sorted(template_words.items())),
                "resilient_records_observed":resilient_records}
    result["scope"]="Fixed headers and bounded witness control fields only; neighbor bounds are not proven extents. No witness entry resolution, pointer authentication or runtime conformance claim."
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    a=p.parse_args()
    if a.image.stat().st_size>MAX_IMAGE:p.error("image too large")
    print(json.dumps(inspect(a.image.read_bytes()),indent=2))
if __name__=="__main__":main()
