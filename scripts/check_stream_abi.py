#!/usr/bin/env python3
"""Compare compiler-generated public functions, never alias protocol data."""
import pathlib,re,sys

targets = [
    "$sScS10makeStream2of15bufferingPolicyScSyxG6stream_ScS12ContinuationVyx_G12continuationtxm_AG09BufferingE0Oyx__GtFZ",
    "$sScs10makeStream2of8throwing15bufferingPolicyScsyxs5Error_pG6stream_Scs12ContinuationVyxsAE_p_G12continuationtxm_sAE_pmAI09BufferingF0OyxsAE_p__GtsAE_pRs_rlFZ",
]
def signatures(ir,kind):
    return re.findall(r'^'+kind+r' ([^\n]*?) @"([^"]+)"\((.*)\) #\d+',ir,re.M)
def abi(ret,args):
    return ret,[re.sub(r' %[A-Za-z0-9_.$-]+$','',a.strip()) for a in args.split(',') if a.strip()]
def only(rows,what):
    if len(rows)!=1: raise SystemExit(f"{what}: expected one symbol, found {rows!r}")
    return rows[0]

stock,candidate=[pathlib.Path(p).read_text() for p in sys.argv[1:3]]
defs=[r for r in signatures(candidate,"define") if r[0].startswith("swiftcc ") and "ioscompatMakeStream" in r[1] and r[1].endswith("FZ")]
if len(defs)!=2: raise SystemExit("Expected two public candidate methods: "+repr(defs))
aliases=[]
for target,prefix in zip(targets,("$sScS","$sScs")):
    a=only([r for r in defs if r[1].startswith(prefix)],prefix)
    b=only([r for r in signatures(stock,"declare") if r[1]==target],target)
    if abi(a[0],a[2])!=abi(b[0],b[2]): raise SystemExit(f"ABI mismatch: {a!r} vs {b!r}")
    aliases.append(("_"+a[1],"_"+target))
    print("Matched",target,abi(a[0],a[2]))
if any(n in targets for _,n,_ in signatures(candidate,"declare")):
    raise SystemExit("Candidate depends on future native target")
pathlib.Path(sys.argv[3]).write_text("".join(a+"\t"+b+"\n" for a,b in aliases))
