#!/usr/bin/env python3
"""Root-scoped system import research queue, based on a local analyzer report."""
import argparse,json
from pathlib import Path
from collections import Counter
from dependency_context import trace
from import_summary import summarize

def classify(report,root):
    if report.get("schema")!=10 or report.get("target")!="16.2":
        raise ValueError("expected schema 10 target 16.2")
    graph=trace(report,root)
    reached=set(graph["reachable_candidates"])
    groups={"root":[],"reachable_dependencies":[],"other_images":[]}
    for image in report["images"]:
        path=image["path"]
        scope="root" if path==root else "reachable_dependencies" if path in reached else "other_images"
        # Preserve evidence but restrict groups to explicit declared system paths.
        groups[scope].append({**image,"imports":[r for r in image.get("imports",[])
            if (r.get("declared_provider") or "").startswith(("/usr/lib/","/System/Library/"))]})
    sections={}
    for scope,images in groups.items():
        s=summarize(images)
        sections[scope]={"image_count":len(images),**s}
    # Combine the root and candidate closure, deduplicating by provider/symbol.
    union=summarize(groups["root"]+groups["reachable_dependencies"])
    return {"schema":1,"target":report["target"],"inventory_build":report.get("inventory_build"),
            "root":root,"scopes":sections,"root_candidate_union":union,
            "graph_limits":graph["limits"],"graph_notes":graph["notes"],
            "scope":"Exact declared system-provider import evidence in the selected candidate graph. Native lookup is sparse and may include reexports or dependencies. Independent candidates are not native providers. Strong imports are not proof of startup failure; other images are not proven unused. No actual dyld binding or compatibility verdict."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("report",type=Path)
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    if a.report.stat().st_size>256*1024*1024:p.error("report too large")
    r=classify(json.loads(a.report.read_text()),a.root)
    with a.output.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2)
    print(json.dumps(r["root_candidate_union"]["counts"],sort_keys=True))
if __name__=="__main__":main()
