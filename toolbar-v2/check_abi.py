#!/usr/bin/env python3
"""Prove both concrete getters match stock ABI and independent SDK fallbacks."""
import pathlib,re,sys

stock,back,candidate=[pathlib.Path(p).read_text() for p in sys.argv[1:4]]
def entries(ir,kind):
    return re.findall(r'^'+kind+r' ([^\n]*?) @"([^"]+)"\((.*)\) #\d+',ir,re.M)
def abi(ret,args):
    return ret,[re.sub(r' %[A-Za-z0-9_.$-]+$','',a.strip()) for a in args.split(',') if a.strip()]
def only(rows,what):
    if len(rows)!=1: raise SystemExit(f"{what}: expected one symbol, found {rows!r}")
    return rows[0]
def body(ir,name):
    return only([x for x in re.findall(r'^define [^\n]+\n.*?^\}',ir,re.M|re.S) if name in x.splitlines()[0]],name)
aliases=[]
for suffix,n in [("Leading",13),("Trailing",14)]:
    target=f"$s7SwiftUI20ToolbarItemPlacementV{n}topBar{suffix}ACvgZ"
    a=only([r for r in entries(candidate,"define") if r[0].startswith("swiftcc ") and "ioscompatTopBar"+suffix in r[1] and r[1].endswith("vgZ")],"candidate")
    b=only([r for r in entries(stock,"declare") if r[1]==target],"stock")
    if abi(a[0],a[2])!=abi(b[0],b[2]):raise SystemExit(f"ABI mismatch: {a!r} vs {b!r}")
    if target in {name for _,name,_ in entries(candidate,"declare")}:raise SystemExit("Recursive future symbol import")
    # Require correct legacy placement in the individual candidate body.
    legacy="navigationBar"+suffix
    wrong="navigationBar"+("Trailing" if suffix=="Leading" else "Leading")
    cb=body(candidate,a[1])
    if legacy not in cb or wrong in cb:raise SystemExit("Candidate legacy dependency mismatch: "+suffix)
    # Back-deployed SDK thunk may be separate from the public wrapper.
    # Require a matching legacy reference in the SDK IR; retain evidence
    # rather than claim visual equivalence.
    if legacy not in back:raise SystemExit("Missing SDK legacy evidence: "+suffix)
    aliases.append("_"+a[1]+"\t_"+target)
    print("MATCHED",suffix,abi(a[0],a[2]))
pathlib.Path(sys.argv[4]).write_text("\n".join(aliases)+"\n")
