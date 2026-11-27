#!/usr/bin/env python3
"""Read-only exact-symbol candidate paths through an IPA's local dependencies."""
import argparse,json,struct,zipfile
from pathlib import Path
from collections import defaultdict,Counter
from analyze_ipa import scan
from dependency_context import trace
from export_trie import inspect_exports

def query(report,graph,exports,symbol):
    # Union of observed contexts, not a reconstruction of actual loader order.
    by_edge=defaultdict(set)
    by_name=defaultdict(set)
    for e in graph["edges"]:
        paths=e["architecture_matching_candidates"]
        by_edge[(e["consumer"],e["ordinal"],e["declared_path"])].update(paths)
        by_name[(e["consumer"],e["declared_path"])].update(paths)
    images={i["path"]:i for i in report["images"]}
    results=[]
    remaining=20000
    for consumer in graph["reachable_candidates"]:
        imports={(r["ordinal"],r["declared_provider"],bool(r["effective_weak"]))
                 for r in images[consumer].get("imports",[]) if r["symbol"]==symbol}
        for ordinal,provider,weak in sorted(imports,key=repr):
            paths=[]
            notes=set()
            if provider is None:
                notes.add("special_or_unknown_ordinal")
            elif provider.startswith(("/usr/lib/","/System/Library/")):
                notes.add("system_provider_not_inspected")
            candidates=by_edge.get((consumer,ordinal,provider),set())
            if not candidates and not notes:
                notes.add("no_local_provider_candidate")
            pending=[(p,symbol,()) for p in sorted(candidates)]
            while pending:
                if remaining<=0 or len(pending)>4096:
                    notes.add("query_budget");break
                remaining-=1
                path,name,chain=pending.pop()
                node=(path,name)
                if node in chain or len(chain)>=64:
                    notes.add("cycle_or_depth");continue
                chain=chain+(node,)
                record=exports.get(path,{})
                if record.get("status")!="trie_inspected":
                    notes.add("export_trie_not_inspected");continue
                entry=record["symbols"].get(name)
                if entry and entry["kind"]!="reexport":
                    paths.append({"chain":[{"image":p,"symbol":n} for p,n in chain],
                                  "terminal_kind":entry["kind"],"weak_definition":entry["weak_definition"]})
                    continue
                providers=[(entry["provider"],entry["import_name"])] if entry else [
                    (p,name) for p in record.get("reexport_libraries",[])]
                for dep,target in providers:
                    children=by_name.get((path,dep),set())
                    if not children:notes.add("reexport_provider_not_inspected")
                    pending.extend((child,target,chain) for child in sorted(children))
            status="local_export_candidate_observed" if paths else "not_observed"
            results.append({"consumer":consumer,"ordinal":ordinal,"declared_provider":provider,
                            "symbol":symbol,"effective_weak":weak,"status":status,
                            "candidate_paths":paths,"notes":sorted(notes)})
            if len(results)>=10000:
                return {"rows":results,"truncated":True}
    return {"rows":results,"truncated":remaining<=0}

def read_exports(ipa,graph):
    records={}
    budget=512*1024*1024
    entries=0
    wanted=set(graph["reachable_candidates"])
    with zipfile.ZipFile(ipa) as z:
        for info in z.infolist():
            if info.filename not in wanted:continue
            if info.file_size>min(budget,256*1024*1024) or entries>=200000:continue
            budget-=info.file_size
            try:
                data=z.read(info)
                if struct.unpack_from("<II",data,4)!=(0x100000c,0):continue
                result=inspect_exports(data)
                entries+=len(result["symbols"])
                if entries<=200000:records[info.filename]=result
            except (ValueError,struct.error,OSError,zipfile.BadZipFile):
                continue
    return records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("ipa",type=Path)
    p.add_argument("--root",required=True)
    p.add_argument("--symbol",required=True,help="Exact raw Mach-O name, including leading underscore")
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    if not a.symbol.startswith("_") or len(a.symbol)>8192:p.error("expected exact raw symbol")
    catalog=json.loads((Path(__file__).parent/"compat_catalog.json").read_text())
    report=scan(a.ipa,catalog)
    graph=trace(report,a.root)
    result=query(report,graph,read_exports(a.ipa,graph),a.symbol)
    result.update(root=a.root,graph_limits=graph["limits"],scope="Union of observed local path contexts, not actual dyld binding. Missing paths or exports remain unobserved, not absent. No system cache, flat namespace, interposition, signing or ABI compatibility proof.")
    result["counts"]=dict(Counter(r["status"] for r in result["rows"]))
    with a.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    print(json.dumps(result["counts"],sort_keys=True))
if __name__=="__main__":main()
