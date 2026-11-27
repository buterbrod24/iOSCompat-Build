"""Convert complete scoped probe reports; preserve unknown and scope differences."""
import argparse,json
from pathlib import Path
from collections import Counter

def convert(text,expected):
    lines=text.splitlines()
    if lines[:3]!=["iOSCompat System Export Probe 0.1.0","OS: Version 16.2 (Build 20C65)","START"]:
        raise ValueError("unexpected report header/build")
    total=sum(map(len,expected.values()))
    if lines[-2:]!=[f"TOTAL\t{total}","COMPLETE"]:
        raise ValueError("incomplete report")
    pos=3
    providers={}
    counts=Counter()
    for provider,names in sorted(expected.items()):
        if pos+2>len(lines) or lines[pos]!="PROVIDER\t"+provider:
            raise ValueError("unexpected provider")
        handles=lines[pos+1].split("\t")
        if len(handles)!=3 or handles[0]!="HANDLES" or any(h not in ("OPEN","UNAVAILABLE") for h in handles[1:]):
            raise ValueError("invalid handles")
        pos+=2
        observations={}
        evidence={}
        for name in names:
            if pos>=len(lines)-2:raise ValueError("missing observation")
            parts=lines[pos].split("\t");pos+=1
            if len(parts)!=4 or parts[:2]!=["LOOKUP",name]:
                raise ValueError("unexpected observation")
            first,tree=parts[2:]
            for state,handle in zip((first,tree),handles[1:]):
                if state not in ("PRESENT","ABSENT","UNKNOWN") or (handle=="UNAVAILABLE" and state!="UNKNOWN"):
                    raise ValueError("invalid lookup state")
            evidence[name]={"first":first.lower(),"tree":tree.lower()}
            counts[first+"/"+tree]+=1
            # Only concordant results enter the analyzer-facing sparse inventory.
            # Mixed scopes may reveal dependency/reexport evidence, not absence.
            if first == tree and first in ("PRESENT", "ABSENT"):
                observations[name]=first.lower()
        providers[provider]={"symbols":observations,"lookup_pairs":evidence,"handles":handles[1:]}
    if pos!=len(lines)-2:raise ValueError("unexpected trailing data")
    return {"schema":1,"target":"16.2","build":"20C65","architecture":"arm64",
            "method":"System Export Probe 0.1.0 concordant RTLD_FIRST and ordinary named-handle lookups; reexports possible; not direct export trie proof",
            "providers":providers,"lookup_pair_counts":dict(counts)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("report",type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    expected=json.loads((Path(__file__).resolve().parents[1]/"system-export-device/queries.json").read_text())
    r=convert(a.report.read_text(encoding="utf-8-sig"),expected)
    with a.output.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2)
    print(json.dumps(r["lookup_pair_counts"],sort_keys=True))
if __name__=="__main__":main()
