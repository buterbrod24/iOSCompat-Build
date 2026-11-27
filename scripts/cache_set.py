#!/usr/bin/env python3
"""Check explicitly supplied cache parts by UUID and unslid mapping ranges."""
import argparse,json,struct,uuid
from pathlib import Path
from cache_inventory import inspect,read_at

def declarations(f):
    size=f.seek(0,2)
    header=read_at(f,size,0,min(size,460))
    if len(header)<104 or not header.startswith(b"dyld_v1"):
        raise ValueError("invalid main cache header")
    extent=struct.unpack_from("<I",header,16)[0]
    if min(extent,len(header))<400:
        return None
    off,count=struct.unpack_from("<II",header,392)
    base=struct.unpack_from("<Q",header,224)[0]
    width=56 if extent>456 else 24
    if count>4096 or (count and off<extent):
        raise ValueError("invalid subcache declarations")
    data=read_at(f,size,off,count*width) if count else b""
    rows=[]
    for i in range(count):
        pos=i*width
        ident=str(uuid.UUID(bytes=data[pos:pos+16]))
        vm=struct.unpack_from("<Q",data,pos+16)[0]
        suffix="."+str(i+1)
        if width==56:
            raw=data[pos+24:pos+56]
            if b"\0" not in raw:
                raise ValueError("unterminated cache suffix")
            suffix=raw.split(b"\0",1)[0].decode("ascii")
            if not suffix.startswith(".") or "/" in suffix or "\\" in suffix or suffix in (".",".."):
                raise ValueError("invalid cache suffix")
        if not vm or base+vm>=1<<64 or not base:
            raise ValueError("invalid declared subcache VM offset")
        rows.append({"uuid":ident,"vm_offset":vm,"suffix":suffix,"expected_start":base+vm})
    for key in ("uuid","suffix","vm_offset"):
        if len({r[key] for r in rows})!=len(rows):
            raise ValueError("duplicate subcache "+key)
    return rows

def verify(main,expected,parts):
    issues=[]
    if expected is None:
        issues.append("subcache declarations unavailable")
    expected=expected or []
    supplied={}
    for part in parts:
        key=part["uuid"]
        if key in supplied or key==main["uuid"]:
            issues.append("duplicate supplied UUID: "+key)
        else:
            supplied[key]=part
    accepted=[main]
    missing=[]
    for row in expected:
        part=supplied.pop(row["uuid"],None)
        if part is None:
            missing.append(row)
            continue
        if part["architecture"]!=main["architecture"]:
            issues.append("architecture mismatch: "+row["uuid"])
            continue
        if any(part.get(k) is not None and main.get(k) is not None and part[k]!=main[k]
               for k in ("platform","os_version")):
            issues.append("platform or OS metadata mismatch: "+row["uuid"])
            continue
        if min(m["address"] for m in part["mappings"])!=row["expected_start"]:
            issues.append("VM start mismatch: "+row["uuid"])
            continue
        accepted.append(part)
    if supplied:
        issues.extend("undeclared supplied UUID: "+x for x in sorted(supplied))
    ranges=sorted((dict(m,cache_uuid=r["uuid"]) for r in accepted for m in r["mappings"]),key=lambda x:x["address"])
    for a,b in zip(ranges,ranges[1:]):
        if a["address"]+a["size"]>b["address"]:
            issues.append("overlapping mappings across cache parts")
    images=[]
    for image in main["images"]:
        owners=[m["cache_uuid"] for m in ranges if m["address"]<=image["address"]<m["address"]+m["size"]]
        images.append(dict(image,cache_owners=owners))
    unmapped=sum(len(x["cache_owners"])!=1 for x in images)
    return {"status":"declared_parts_matched" if not issues and not missing and not unmapped else "incomplete_or_unverified",
            "expected_parts":len(expected),"accepted_parts":len(accepted)-1,
            "missing":missing,"issues":sorted(set(issues)),"unmapped_or_ambiguous_images":unmapped,
            "images":images,"mappings":ranges,
            "scope":"UUID and mapping metadata only; no signature validation, exports or runtime compatibility verdict"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("main",type=Path)
    p.add_argument("parts",type=Path,nargs="*")
    a=p.parse_args()
    with a.main.open("rb") as f:
        root=inspect(f)
        expected=declarations(f)
    parts=[]
    for path in a.parts:
        with path.open("rb") as f: parts.append(inspect(f))
    print(json.dumps(verify(root,expected,parts),indent=2))
if __name__=="__main__":
    main()
