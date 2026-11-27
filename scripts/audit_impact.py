#!/usr/bin/env python3
"""Measure exact runtime-symbol consumer overlap in a local selected-export audit."""
import argparse,json
from collections import Counter
from pathlib import Path
from audit_coverage import read_audit

PROVIDER="/usr/lib/swift/libswiftCore.dylib"
NAMES=(
    "swift_conformsToProtocol2",
    "swift_getOpaqueTypeConformance2",
    "swift_getOpaqueTypeMetadata2",
    "swift_getTypeByMangledNameInContext2",
    "swift_getTypeByMangledNameInContextInMetadataState2",
)

def impact(rows):
    by_name={name:rows.get((PROVIDER,name)) for name in NAMES}
    consumers=set()
    counts=Counter()
    symbols={}
    for name,row in by_name.items():
        if row is None:
            symbols[name]={"status":"not_observed_in_report"}
            continue
        paths=row["consumers"]
        consumers.update(paths)
        counts.update(paths)
        symbols[name]={"status":"observed","consumers":len(paths),
                       "group_strength":"strong" if row["required"] else "weak_only"}
    histogram=Counter(counts.values())
    return {"schema":1,"provider":PROVIDER,"symbols":symbols,
            "unique_consumers":len(consumers),"symbol_consumer_pairs":sum(counts.values()),
            "overlap_histogram":dict(sorted(histogram.items())),
            "note":"Group strength is aggregate, not per-consumer strength. Omitted symbols are not proven absent. Consumer names are not exported. No loader or execution verdict."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("audit",type=Path)
    a=p.parse_args()
    if a.audit.stat().st_size>16*1024*1024:
        p.error("audit exceeds input limit")
    print(json.dumps(impact(read_audit(a.audit.read_text())),indent=2))
if __name__=="__main__":
    main()
