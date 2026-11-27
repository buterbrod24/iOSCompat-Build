#!/usr/bin/env python3
"""Classify Swift ABI symbol roles using the compiler's demangler, never suffix guesses."""
import argparse,collections,json,re,subprocess
from pathlib import Path

CALLABLE={"Function","Allocator","Constructor","Getter","Setter","ModifyAccessor","ReadAccessor"}
DATA={"NominalTypeDescriptor","ProtocolDescriptor","ProtocolConformanceDescriptor",
      "OpaqueTypeDescriptor","MethodDescriptor","AssociatedTypeDescriptor",
      "AssociatedConformanceDescriptor","BaseConformanceDescriptor","ProtocolRequirementsBaseDescriptor",
      "ProtocolWitnessTable","ValueWitnessTable","TypeMetadata"}
def classify(nodes,children):
    if len(nodes)!=1: return "unclassified"
    kind=nodes[0]
    if kind=="Static":
        return "ordinary_callable" if len(children)==1 and children[0] in CALLABLE else "unclassified"
    if kind in CALLABLE: return "ordinary_callable"
    if kind=="TypeMetadataAccessFunction": return "metadata_accessor"
    if kind=="DispatchThunk": return "dispatch_thunk"
    if kind in DATA: return "abi_data"
    return "unclassified"

def demangle(names,tool="swift-demangle"):
    names=sorted(set(n[1:] if n.startswith("_$s") else n for n in names
                     if n.startswith(("$s","_$s"))))
    if len(names)>20000 or any(len(n)>8192 or not re.fullmatch(r"\$s[A-Za-z0-9_$]+",n) for n in names):
        raise ValueError("unsupported symbol input or budget")
    result=[]
    for i in range(0,len(names),100):
        batch=names[i:i+100]
        out=subprocess.run([tool,"--expand","--compact"],input="\n".join(batch)+"\n",
                           text=True,capture_output=True,check=True,timeout=60).stdout
        blocks=re.split(r"^Demangling for ",out,flags=re.M)[1:]
        if len(blocks)!=len(batch): raise ValueError("unexpected demangler output count")
        for expected,block in zip(batch,blocks):
            lines=block.splitlines()
            if lines[0]!=expected: raise ValueError("unexpected demangler symbol identity")
            roots=re.findall(r"^kind=(\w+)",block,re.M)
            nodes=re.findall(r"^  kind=(\w+)",block,re.M)
            children=re.findall(r"^    kind=(\w+)",block,re.M)
            role=classify(nodes,children) if roots==["Global"] else "unclassified"
            result.append({"symbol":expected,"nodes":nodes,"role":role,
                           "label":lines[-1] if len(lines)>1 else expected})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbols",type=Path,help="Local text file containing one mangled symbol per line")
    p.add_argument("--demangler",default="swift-demangle")
    a=p.parse_args()
    rows=demangle(a.symbols.read_text().splitlines(),a.demangler)
    print(json.dumps({"roles":dict(collections.Counter(r["role"] for r in rows)),
                      "nodes":dict(collections.Counter("+".join(r["nodes"]) or "unknown" for r in rows)),
                      "symbols":rows,
                      "scope":"Demangler structural evidence only; no ABI compatibility or implementation feasibility verdict"},indent=2))
if __name__=="__main__":
    main()
