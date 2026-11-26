#!/usr/bin/env python3
"""Read upstream ABI macros with balanced parentheses; fail closed on missing evidence."""
import json,pathlib,re,sys

names=["swift_conformsToProtocol","swift_getOpaqueTypeMetadata","swift_getOpaqueTypeConformance","swift_getTypeByMangledNameInContext","swift_getTypeByMangledNameInContextInMetadataState"]

def split_args(s):
    out=[]; start=0; depth=0
    for i,c in enumerate(s):
        if c=="(": depth+=1
        elif c==")": depth-=1
        elif c=="," and depth==0: out.append(s[start:i].strip());start=i+1
    out.append(s[start:].strip())
    return out

def macros(s):
    s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
    for m in re.finditer(r'\bFUNCTION\s*\(',s):
        start=m.end();depth=1
        for i in range(start,len(s)):
            if s[i]=="(":depth+=1
            elif s[i]==")":
                depth-=1
                if depth==0:
                    args=split_args(s[start:i])
                    if len(args)>=7:yield args
                    break

def parse(path):
    result={}
    for args in macros(pathlib.Path(path).read_text()):
        name=args[1]
        if name in names or name in {n+"2" for n in names}:
            result[name]={"macroID":args[0],"callingConvention":args[2],"availability":args[3],
                          "returns":next((x for x in args if x.startswith("RETURNS(")),None),
                          "arguments":next((x for x in args if x.startswith("ARGS(")),None)}
    return result

old,new=map(parse,sys.argv[1:3])
report=[]
for name in names:
    legacy=old.get(name);modern=new.get(name+"2")
    if not legacy or not modern: raise SystemExit("Missing required upstream evidence: "+name+" "+str((bool(legacy),bool(modern))))
    if not all(row[k] for row in (legacy,modern) for k in ("returns","arguments")): raise SystemExit("Incomplete declaration: "+name)
    same=all(re.sub(r"\s+","",legacy[k])==re.sub(r"\s+","",modern[k]) for k in ("callingConvention","returns","arguments"))
    print(name, "same declared ABI:",same,"availability:",legacy["availability"],"->",modern["availability"])
    report.append({"symbol":name,"legacy":legacy,"modern":modern,"sameDeclaredABI":same,
                   "status":"RESEARCH_ONLY","reason":"Descriptor and witness semantics not established by matching declarations"})
pathlib.Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+"\n")
print("Five declaration pairs found; no replacement symbols emitted.")
