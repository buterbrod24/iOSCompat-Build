"""Read-only Swift back-deployment name evidence, not control-flow analysis."""
import struct

def inspect_markers(data):
    if len(data)<32 or struct.unpack_from("<I",data)[0]!=0xfeedfacf:
        raise ValueError("not thin Mach-O 64")
    ncmd,size=struct.unpack_from("<II",data,16)
    if size>len(data)-32 or ncmd>size//8:
        raise ValueError("invalid load commands")
    pos=32
    table=None
    for _ in range(ncmd):
        if pos+8>32+size:
            raise ValueError("truncated load command")
        cmd,length=struct.unpack_from("<II",data,pos)
        if length<8 or length%8 or pos+length>32+size:
            raise ValueError("invalid load command")
        if cmd==2:
            if length<24 or table is not None:
                raise ValueError("invalid symbol table command")
            table=struct.unpack_from("<4I",data,pos+8)
        pos+=length
    if pos!=32+size:
        raise ValueError("load command size mismatch")
    result={"scope":"Defined nlist section symbols only; no reachability or fallback behavior inference",
            "symbol_table":"unavailable","markers":[]}
    if table is None:
        return result
    so,count,st,sz=table
    if so+count*16>len(data) or st+sz>len(data):
        raise ValueError("symbol table outside image")
    if count>2_000_000 or sz>64*1024*1024:
        result["symbol_table"]="budget_exceeded"
        return result
    result["symbol_table"]="inspected" if count else "empty"
    pool=data[st:st+sz]
    markers={}
    for i in range(count):
        off,typ,sect,desc,value=struct.unpack_from("<IBBHQ",data,so+i*16)
        # Exclude STAB, undefined and absolute symbols; include locals.
        if typ&0xe0 or typ&0x0e!=0x0e or not sect or not off:
            continue
        if off>=sz:
            raise ValueError("invalid symbol name offset")
        if pool[off:off+3]!=b"_$s":
            continue
        end=pool.find(b"\0",off)
        if end<0:
            raise ValueError("unterminated Swift symbol")
        raw=pool[off:end]
        suffix=raw[-3:]
        if suffix not in (b"Twb",b"TwB"):
            continue
        name=raw.decode("utf-8","replace")
        stem=name[:-3]
        entry=markers.setdefault(stem,{"stem":stem,"thunk":[],"fallback":[]})
        key="thunk" if suffix==b"Twb" else "fallback"
        if name not in entry[key]:
            entry[key].append(name)
    result["markers"]=[markers[k] for k in sorted(markers)]
    return result

def annotate_imports(image):
    # Only exact syntactic stem matches in the same image, never cross-image proof.
    stems={row["stem"]:row for row in image.get("backdeploy",{}).get("markers",[])}
    for row in image.get("imports",[]):
        match=stems.get(row["symbol"])
        row["backdeploy_name_evidence"]=(
            "thunk_and_fallback_names" if match and match["thunk"] and match["fallback"]
            else "partial_name_match" if match else "not_observed")
