#!/usr/bin/env python3
"""Compare a local selected-export audit with exact provider-qualified catalog evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

def read_audit(text):
    if len(text)>16*1024*1024:
        raise ValueError("audit exceeds input limit")
    if text.count("\nSYMBOL DETAILS\n")!=1:
        raise ValueError("expected exactly one SYMBOL DETAILS section")
    header,detail=text.split("\nSYMBOL DETAILS\n")
    totals=re.findall(r"^Distinct symbols: (\d+); per-binary records: (\d+); strong distinct: (\d+)\.$",header,re.M)
    if len(totals)!=1:
        raise ValueError("missing or ambiguous audit totals")
    expected=tuple(map(int,totals[0]))
    rows={}
    current=None
    for line in detail.splitlines():
        if not line.strip():
            continue
        if line.startswith("  "):
            if current is None or not line[2:].strip():
                raise ValueError("orphaned consumer")
            consumer=line[2:]
            if consumer in rows[current]["consumers"]:
                raise ValueError("duplicate consumer")
            rows[current]["consumers"].add(consumer)
            continue
        fields=line.split(" | ")
        if len(fields)!=3:
            raise ValueError("unexpected symbol detail format")
        provider,strength,raw=fields
        if not provider.startswith("/") or strength not in ("strong","weak only") or not raw.startswith("_") or len(raw)<2 or any(c.isspace() for c in raw):
            raise ValueError("invalid symbol detail")
        current=(provider,raw[1:])
        if current in rows:
            raise ValueError("duplicate provider/symbol")
        rows[current]={"required":strength=="strong","consumers":set()}
    if not rows or any(not row["consumers"] for row in rows.values()):
        raise ValueError("empty audit or missing consumer")
    actual=(len(rows),sum(len(row["consumers"]) for row in rows.values()),sum(row["required"] for row in rows.values()))
    if actual!=expected:
        raise ValueError(f"audit totals mismatch: {actual} != {expected}")
    return rows

def compare(rows,catalog):
    if catalog.get("schema")!=1 or catalog.get("target")!="16.2" or not isinstance(catalog.get("symbols"),dict):
        raise ValueError("unsupported catalog schema or target")
    allowed={"missing_unresolved","candidate_device_tested",
             "candidate_independent_device_tested","candidate_internal_device_tested_stock_linked"}
    for symbol,item in catalog["symbols"].items():
        if not isinstance(item,dict) or item.get("status") not in allowed or not isinstance(item.get("provider"),str):
            raise ValueError("unrecognized catalog entry")
    buckets=Counter()
    providers={}
    matches=[]
    for (provider,symbol),row in sorted(rows.items()):
        entry=catalog["symbols"].get(symbol)
        if entry is None:
            status="not_cataloged"
        elif entry["provider"]!=provider:
            status="provider_mismatch"
        else:
            status=entry["status"]
            matches.append({"provider":provider,"symbol":symbol,"status":status,"required":row["required"]})
        strength="strong" if row["required"] else "weak_only"
        buckets[(status,strength)]+=1
        counts=providers.setdefault(provider,Counter())
        counts[(status,strength)]+=1
    def nested(counts):
        return {s:{"strong":counts[s,"strong"],"weak_only":counts[s,"weak_only"]}
                for s in sorted({s for s,_ in counts})}
    return {"schema":1,"target":catalog["target"],
            "symbols":len(rows),"strong":sum(r["required"] for r in rows.values()),
            "consumer_records":sum(len(r["consumers"]) for r in rows.values()),
            "evidence":nested(buckets),"providers":{p:nested(c) for p,c in sorted(providers.items())},
            "exact_catalog_matches":matches,
            "note":"Selected-export audit only, not a loader or compatibility verdict. Device-tested candidates are not proven app integrations. Source-only adapters intentionally not counted."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("audit",type=Path)
    p.add_argument("--catalog",type=Path,default=Path(__file__).with_name("compat_catalog.json"))
    p.add_argument("--details",action="store_true",help="Include exact catalog-matched symbol names")
    a=p.parse_args()
    if a.audit.stat().st_size>16*1024*1024:
        p.error("audit exceeds input limit")
    result=compare(read_audit(a.audit.read_text()),json.loads(a.catalog.read_text()))
    if not a.details:
        result.pop("exact_catalog_matches")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
