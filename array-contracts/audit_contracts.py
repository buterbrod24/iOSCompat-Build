#!/usr/bin/env python3
"""Compare upstream source contracts, not binary layout or runtime compatibility."""
import hashlib
import pathlib
import re
import sys

METHODS = {
    "Array.swift": ["_endMutation", "_makeUniqueAndReserveCapacityIfNotUnique",
                    "_reserveCapacityAssumingUniqueBuffer", "_appendElementAssumeUniqueAndCapacity",
                    "_reserveCapacityImpl", "_createNewBuffer"],
    "ContiguousArray.swift": ["_endMutation", "_makeUniqueAndReserveCapacityIfNotUnique",
                              "_reserveCapacityAssumingUniqueBuffer", "_appendElementAssumeUniqueAndCapacity",
                              "_reserveCapacityImpl"],
    "ArrayBuffer.swift": ["_getElementSlowPath", "_consumeAndCreateNew"],
    "ContiguousArrayBuffer.swift": ["_consumeAndCreateNew"],
}

def extract(source, name):
    lines=source.splitlines()
    hits=[]
    pattern=re.compile(r"\bfunc "+re.escape(name)+r"\(")
    for i,line in enumerate(lines):
        if not pattern.search(line):
            continue
        start=i
        while start and lines[start-1].lstrip().startswith("@"):
            start-=1
        # These pinned sources use a standalone closing brace at the same
        # indentation as the declaration. Reject incomplete or ambiguous matches.
        indent=line[:len(line)-len(line.lstrip())]
        end=next((j for j in range(i+1,len(lines)) if lines[j]==indent+"}"),None)
        if end is None:
            raise ValueError("unclosed function "+name)
        block="\n".join(lines[i:end+1])
        if name=="_consumeAndCreateNew" and not re.search(r"func _consumeAndCreateNew\(\s*bufferIsUnique:",block):
            continue
        declaration,sep,body=block.partition("{")
        if not sep:
            raise ValueError("no body "+name)
        hits.append(( "\n".join(lines[start:i]).strip(), declaration.strip(), body.strip()))
    if len(hits)!=1:
        raise ValueError(f"{name}: expected one contract, found {len(hits)}")
    return hits[0]

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def main():
    old,new=map(pathlib.Path,sys.argv[1:3])
    count=0
    for filename,names in METHODS.items():
        a=(old/filename).read_text()
        b=(new/filename).read_text()
        for name in names:
            left,right=extract(a,name),extract(b,name)
            print(f"{filename}:{name} annotations={'same' if left[0]==right[0] else 'changed'} declaration={'same' if left[1]==right[1] else 'changed'} body={'same' if left[2]==right[2] else 'changed'}")
            print("  body SHA256:",digest(left[2]),digest(right[2]))
            count+=1
    print("SOURCE CONTRACTS",count,"/14")
    print("Private buffer mutation, ownership and compiler semantics are not interchangeable with public Array API calls.")
    print("No replacement symbols or private memory layout assumptions are generated.")
    if count!=14: raise SystemExit(1)

if __name__=="__main__":
    main()
