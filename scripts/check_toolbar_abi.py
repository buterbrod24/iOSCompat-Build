#!/usr/bin/env python3
"""Gate the exact callable only; no fabricated SwiftUI metadata."""
import pathlib,re,sys

target="$s7SwiftUI20ToolbarItemPlacementV13topBarLeadingACvgZ"
legacy="$s7SwiftUI20ToolbarItemPlacementV20navigationBarLeadingACvgZ"
stock,back,candidate=[pathlib.Path(p).read_text() for p in sys.argv[1:4]]
def entries(ir,kind):
    return re.findall(r'^'+kind+r' ([^\n]*?) @"([^"]+)"\((.*)\) #\d+',ir,re.M)
def abi(ret,args):
    return ret,[re.sub(r' %[A-Za-z0-9_.$-]+$','',a.strip()) for a in args.split(',') if a.strip()]
def only(rows,what):
    if len(rows)!=1: raise SystemExit(f"{what}: expected one symbol, found {rows!r}")
    return rows[0]
a=only([r for r in entries(candidate,"define") if r[0].startswith("swiftcc ") and "ioscompatTopBarLeading" in r[1] and r[1].endswith("vgZ")],"candidate")
b=only([r for r in entries(stock,"declare") if r[1]==target],"stock")
if abi(a[0],a[2])!=abi(b[0],b[2]): raise SystemExit(f"ABI mismatch: {a!r} vs {b!r}")
if target in {n for _,n,_ in entries(candidate,"declare")}: raise SystemExit("Recursive future symbol import")
# A let may be lowered as its getter or a native global/unsafe addressor.
if "navigationBarLeading" not in candidate: raise SystemExit("No legacy native placement dependency")
if "navigationBarLeading" not in back: raise SystemExit("SDK fallback must independently reference native legacy placement")
print("MATCHED callable ABI:",abi(a[0],a[2]))
print("SDK back-deployment and candidate both reference navigationBarLeading")
pathlib.Path(sys.argv[4]).write_text("_"+a[1]+"\t_"+target+"\n")
