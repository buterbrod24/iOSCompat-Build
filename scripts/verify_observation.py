#!/usr/bin/env python3
"""Read-only verifier for the exact Observation device-tested artifact. No extraction to disk."""
import argparse, hashlib, io, json, pathlib, struct, zipfile
from macho_imports import read_dependencies

ROOT=pathlib.Path(__file__).resolve().parent.parent
PIN=ROOT/"component-manifests/observation-0.2.0.json"
CATALOG=ROOT/"scripts/compat_catalog.json"
IPA="iOSCompat-ObservationProbe-0.2.0.ipa"
LIB="Payload/ObservationStockProbe.app/Frameworks/libObservationResearch.dylib"
LIMIT=16*1024*1024

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def member(z, name):
    hits=[i for i in z.infolist() if i.filename==name]
    require(len(hits)==1 and not hits[0].is_dir(),"missing or duplicate member: "+name)
    require(hits[0].file_size<=LIMIT,"member exceeds budget")
    return z.read(hits[0])

def inspect(data, manifest):
    require(len(data)==manifest["library_bytes"] and sha(data)==manifest["library_sha256"],"library digest or length mismatch")
    magic,cpu,subtype,kind,ncmd,size,flags,reserved=struct.unpack_from("<8I",data)
    require((magic,cpu,subtype&0xffffff,kind)==(0xfeedfacf,0x100000c,0,6),"not ordinary ARM64 MH_DYLIB")
    deps,_=read_dependencies(data)
    require([d["path"] for d in deps]==manifest["dependencies"],"dependency list mismatch")
    require(all(d["path"]!="/usr/lib/swift/libswiftObservation.dylib" for d in deps),"system Observation dependency")
    pos=32
    names=[]
    builds=[]
    for _ in range(ncmd):
        cmd,length=struct.unpack_from("<II",data,pos)
        require(length>=8 and pos+length<=32+size,"invalid command")
        if cmd==0xd:
            require(length>=24,"short LC_ID_DYLIB")
            off=struct.unpack_from("<I",data,pos+8)[0]
            require(24<=off<length,"invalid install name")
            raw=data[pos+off:pos+length]
            require(b"\0" in raw,"unterminated install name")
            names.append(raw.split(b"\0",1)[0].decode("utf-8"))
        if cmd==0x32:
            require(length>=24,"short LC_BUILD_VERSION")
            platform,minimum=struct.unpack_from("<II",data,pos+8)
            builds.append((platform,minimum))
        pos+=length
    require(names==[manifest["install_name"]],"install name mismatch")
    require(builds==[(2,(16<<16)|(2<<8))],"iOS deployment target mismatch")
    return {"architecture":"arm64","minimum_ios":"16.2","install_name":names[0],"dependencies":deps,"library_sha256":sha(data),"library_bytes":len(data)}

def catalog_gate(manifest,catalog):
    names=manifest["required_symbols"]
    expected={k for k,v in catalog["symbols"].items() if v["provider"]=="/usr/lib/swift/libswiftObservation.dylib" and v["status"]=="candidate_independent_device_tested"}
    require(catalog["target"]=="16.2" and len(names)==9 and set(names)==expected,"catalog evidence mismatch")
    return len(names)

def verify(artifact,manifest,catalog):
    count=catalog_gate(manifest,catalog)
    require(len(artifact)<=LIMIT and sha(artifact)==manifest["artifact_sha256"],"artifact digest mismatch")
    with zipfile.ZipFile(io.BytesIO(artifact)) as outer:
        ipa=member(outer,IPA)
    require(sha(ipa)==manifest["ipa_sha256"],"IPA digest mismatch")
    with zipfile.ZipFile(io.BytesIO(ipa)) as inner:
        data=member(inner,LIB)
        for suffix in ("Observation-LICENSE.txt","Observation-NOTICE.txt"):
            name=LIB.split("/Frameworks/")[0]+"/"+suffix
            require(bool(member(inner,name).strip()),"empty license or notice")
    result=inspect(data,manifest)
    result["catalog_symbols"]=count
    result["scope"]="Exact validated artifact provenance, not a fresh export-trie or application runtime test"
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact",type=pathlib.Path)
    args=parser.parse_args()
    require(args.artifact.stat().st_size<=LIMIT,"artifact exceeds budget")
    result=verify(args.artifact.read_bytes(),json.loads(PIN.read_text()),json.loads(CATALOG.read_text()))
    print(json.dumps(result,indent=2))
    print("PASS exact validated Observation component")

if __name__=="__main__":
    main()
