#!/usr/bin/env python3
"""Conservative local dependency candidates in an explicitly selected process context."""
import argparse,json,posixpath
from collections import Counter,deque
from pathlib import Path

MAX_CONTEXTS=4096
MAX_EDGES=20000
MAX_RUNPATHS=128

def valid_path(p):
    return isinstance(p,str) and p.startswith("Payload/") and p==posixpath.normpath(p) and "\\" not in p and "\0" not in p

def join(base,suffix):
    p=posixpath.normpath(posixpath.join(base,suffix))
    return p if valid_path(p) else None

def expand(path,loader,root):
    for prefix,base in (("@loader_path",loader),("@executable_path",root)):
        if path==prefix:return base
        if path.startswith(prefix+"/"):return join(base,path[len(prefix)+1:])
    return None

def trace(report,root):
    images={}
    for image in report["images"]:
        path=image["path"]
        if not valid_path(path) or path in images:
            raise ValueError("ambiguous or invalid archive image path")
        images[path]=image
    if root not in images or "error" in images[root]:
        raise ValueError("explicit root is not an inspected image")
    arch=(images[root].get("cpu_type"),images[root].get("cpu_subtype"))
    if arch!=(0x100000c,0):
        raise ValueError("only ordinary ARM64 root supported")
    root_dir=posixpath.dirname(root)
    pending=deque([(root,())])
    seen=set()
    reached=set()
    edges=[]
    limits=set()
    blockers=Counter()
    while pending:
        path,inherited=pending.popleft()
        node=(path,inherited)
        if node in seen:continue
        if len(seen)>=MAX_CONTEXTS:
            limits.add("context_budget");break
        seen.add(node)
        reached.add(path)
        image=images[path]
        loader=posixpath.dirname(path)
        own=[]
        unknown_rpaths=0
        for rp in image.get("rpaths",[]):
            p=expand(rp,loader,root_dir)
            if p is None:unknown_rpaths+=1
            elif p not in own:own.append(p)
        if unknown_rpaths:blockers["unsupported_rpath_declarations"]+=unknown_rpaths
        # Keep distinct roots in encounter order, not a dyld precedence claim.
        stack=tuple(dict.fromkeys(own+list(inherited)))
        if len(stack)>MAX_RUNPATHS:
            limits.add("runpath_budget");continue
        for dep in image.get("dependencies",[]):
            if len(edges)>=MAX_EDGES:
                limits.add("edge_budget");break
            name=dep["path"]
            candidates=set()
            if name.startswith("@rpath/"):
                for base in stack:
                    p=join(base,name[len("@rpath/"):])
                    if p in images:candidates.add(p)
            else:
                p=expand(name,loader,root_dir)
                if p in images:candidates.add(p)
            if name.startswith(("/usr/lib/","/System/Library/")):
                status="system_unverified"
            elif not candidates:
                status="no_local_candidate_observed"
            else:
                status="local_candidates_observed"
            compatible=[]
            uninspected=[]
            for candidate in sorted(candidates):
                entry=images[candidate]
                if "error" in entry or (entry.get("cpu_type"),entry.get("cpu_subtype"))!=arch:
                    uninspected.append(candidate)
                else:compatible.append(candidate)
            edges.append({"consumer":path,"declared_path":name,"ordinal":dep.get("ordinal"),
                          "kind":dep.get("kind"),"status":status,"runpath_candidates":list(stack),
                          "architecture_matching_candidates":compatible,"uninspected_or_other_arch":uninspected})
            for candidate in compatible:
                if len(pending)>=MAX_CONTEXTS:
                    limits.add("pending_budget");break
                if (candidate,stack) not in seen:pending.append((candidate,stack))
        if "edge_budget" in limits:break
    return {"schema":1,"root":root,"contexts":len(seen),"reachable_candidates":sorted(reached),
            "other_images":sorted(set(images)-reached),"edges":edges,
            "edge_counts":dict(sorted(Counter(e["status"] for e in edges).items())),
            "limits":sorted(limits),"notes":dict(blockers),
            "scope":"Candidate graph, not dyld resolution or startup order. All matching local paths are explored, including weak/lazy/upward edges. Other images may be loaded dynamically or via separate process roots. System paths, absolute runpaths, symlinks, code signing, install-name aliases and loadability not verified."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("report",type=Path)
    p.add_argument("--root",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.report.stat().st_size>256*1024*1024:p.error("report too large")
    result=trace(json.loads(a.report.read_text()),a.root)
    with a.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    print("Candidate images:",len(result["reachable_candidates"]),"contexts:",result["contexts"])
if __name__=="__main__":main()
