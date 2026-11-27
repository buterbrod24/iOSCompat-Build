#!/usr/bin/env python3
"""Compare selected provider export metadata from two local cache sets."""
import argparse,json,struct
from contextlib import ExitStack
from pathlib import Path
from cache_inventory import inspect
from cache_set import declarations,verify
from cache_exports import VMReader,inspect_image

def snapshot(main,parts,providers):
    if not providers or len(providers)>64 or len(set(providers))!=len(providers):
        raise ValueError("supply 1 to 64 distinct provider paths")
    if any(not p.startswith("/") for p in providers):
        raise ValueError("provider paths must be absolute install names")
    with ExitStack() as stack:
        f=stack.enter_context(main.open("rb"))
        root=inspect(f)
        expected=declarations(f)
        files={root["uuid"]:(f,f.seek(0,2))}
        records=[]
        for path in parts:
            handle=stack.enter_context(path.open("rb"))
            r=inspect(handle)
            if r["uuid"] in files: raise ValueError("duplicate cache UUID")
            records.append(r)
            files[r["uuid"]]=(handle,handle.seek(0,2))
        matched=verify(root,expected,records)
        if matched["status"]!="declared_parts_matched":
            raise ValueError("cache set incomplete or unverified")
        if root["platform"]!=2 or root["os_version"] is None:
            raise ValueError("iOS platform/version metadata unverified")
        reader=VMReader(matched["mappings"],files)
        result={"schema":1,"cache_uuid":root["uuid"],"architecture":root["architecture"],
                "platform":root["platform"],"os_version":root["os_version"],"providers":{},
                "scope":"Selected cache export tries only; no runtime binding or ABI verdict"}
        index={}
        for image in root["images"]:
            index.setdefault(image["path"],[]).append(image["address"])
        for provider in providers:
            addresses=index.get(provider,[])
            if len(addresses)!=1:
                result["providers"][provider]={"status":"provider_unindexed_or_ambiguous"}
                continue
            try:
                entry=inspect_image(reader,addresses[0])
                if entry["install_name"]!=provider:
                    entry={"status":"install_name_mismatch","observed_install_name":entry["install_name"]}
            except (ValueError,struct.error,OSError) as exc:
                entry={"status":"uninspected_error","error":str(exc)}
            result["providers"][provider]=entry
        return result

def compare(old,new):
    for snap in (old,new):
        if snap.get("schema")!=1 or snap.get("platform")!=2 or snap.get("architecture") not in ("arm64","arm64e"):
            raise ValueError("unsupported snapshot schema/platform/architecture")
        if not isinstance(snap.get("providers"),dict) or not snap.get("cache_uuid"):
            raise ValueError("missing snapshot provenance")
        version=snap.get("os_version")
        if not isinstance(version,list) or len(version)!=3 or any(type(v)!=int or v<0 for v in version):
            raise ValueError("invalid version")
    if old["architecture"]!=new["architecture"]:
        raise ValueError("cross-architecture comparison unsupported")
    if old["os_version"]>=new["os_version"]:
        raise ValueError("newer iOS version must follow older version")
    result={"schema":1,"older_uuid":old["cache_uuid"],"newer_uuid":new["cache_uuid"],
            "architecture":old["architecture"],"older_os":old["os_version"],"newer_os":new["os_version"],
            "providers":{},"scope":"Direct trie-entry comparison only; reexport reachability and ABI not proven"}
    for path in sorted(set(old["providers"])|set(new["providers"])):
        a=old["providers"].get(path,{})
        b=new["providers"].get(path,{})
        row={"older_status":a.get("status","unselected"),"newer_status":b.get("status","unselected")}
        if any(r.get("status")!="trie_inspected" or r.get("install_name")!=path for r in (a,b)):
            row["status"]="not_comparable"
        elif a.get("architecture")!=b.get("architecture"):
            row["status"]="image_architecture_mismatch"
        else:
            aa,bb=a["symbols"],b["symbols"]
            added=sorted(bb.keys()-aa.keys())
            removed=sorted(aa.keys()-bb.keys())
            changed=[{"name":n,"older":aa[n],"newer":bb[n]} for n in sorted(aa.keys()&bb.keys()) if aa[n]!=bb[n]]
            ar=set(a.get("reexport_libraries",[]))
            br=set(b.get("reexport_libraries",[]))
            row.update(status="compared",newer_only_entries=added,older_only_entries=removed,
                       changed_entries=changed,unchanged_entry_count=len(aa.keys()&bb.keys())-len(changed),
                       newer_reexport_declarations=sorted(br-ar),older_reexport_declarations=sorted(ar-br))
        result["providers"][path]=row
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("snapshot")
    s.add_argument("main",type=Path)
    s.add_argument("parts",type=Path,nargs="*")
    s.add_argument("--provider",action="append",required=True)
    c=sub.add_parser("compare")
    c.add_argument("older",type=Path)
    c.add_argument("newer",type=Path)
    a=p.parse_args()
    if a.command=="snapshot":
        result=snapshot(a.main,a.parts,a.provider)
    else:
        result=compare(json.loads(a.older.read_text()),json.loads(a.newer.read_text()))
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
