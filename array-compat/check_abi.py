#!/usr/bin/env python3
"""Compare compiler-generated calling convention and ABI argument attributes."""
import pathlib,re,sys

target="$ss15ContiguousArrayV15reserveCapacityyySiFyXl_Ts5"
stock,candidate=map(lambda p:pathlib.Path(p).read_text(),sys.argv[1:3])
pattern=r'^(define|declare)\s+(.*?)@"([^"]+)"\('
def entries(ir):
    rows=[]
    for m in re.finditer(pattern,ir,re.M):
        depth=1
        for i in range(m.end(),len(ir)):
            ch=ir[i]
            if ch=="(":
                depth+=1
            elif ch==")":
                depth-=1
                if depth==0:
                    rows.append((*m.groups(),ir[m.end():i]))
                    break
            if ch=="\n":raise SystemExit("Unexpected multiline LLVM signature: "+m[3])
        else:raise SystemExit("Unclosed signature: "+m[3])
    return rows
def find(rows,kind,predicate):
    hits=[(ret,name,args) for k,ret,name,args in rows if k==kind and predicate(name) and "swiftcc" in ret]
    if len(hits)!=1:raise SystemExit("Expected one "+kind+": "+repr(hits))
    return hits[0]
def abi(row):
    ret,name,args=row
    result=[]
    for arg in args.split(","):
        arg=re.sub(r'\s+%[-\w.$]+$','',arg.strip())
        # Optimization hints need not match; the type, swiftself and ownership
        # attributes must. Keep dereferenceable and alignment separately in log.
        arg=re.sub(r'\b(?:nocapture|noundef|nonnull|readonly|writeonly)\b','',arg)
        arg=re.sub(r'\b(?:dereferenceable(?:_or_null)?\(\d+\)|align \d+)','',arg)
        result.append(" ".join(arg.split()))
    return (" ".join(ret[ret.index("swiftcc"):].split()),result)
a=find(entries(stock),"declare",lambda n:n==target)
b=find(entries(candidate),"define",lambda n:"ioscompatReserveCapacity" in n)
print("Stock:",a)
print("Candidate:",b)
if abi(a)!=("swiftcc void",["i64","ptr swiftself"]):raise SystemExit("Unexpected stock ABI: "+repr(abi(a)))
if abi(a)!=abi(b):raise SystemExit("ABI mismatch: "+repr((abi(a),abi(b))))
if target in candidate:raise SystemExit("Candidate refers to future specialized symbol")
future=[n for k,_,n,_ in entries(candidate) if k=="declare" and n.endswith("Ts5")]
if future:raise SystemExit("Candidate imports specialized runtime functions: "+repr(future))
print("MATCHED callable ABI:",abi(b))
pathlib.Path(sys.argv[3]).write_text("_"+b[1]+"\t_"+target+"\n")
