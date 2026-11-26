#!/usr/bin/env python3
"""Report compiler-emitted specialized imports. Do not equate absence with compatibility."""
import json,pathlib,re,sys

names=[
"_makeUniqueAndReserveCapacityIfNotUnique","_createNewBuffer",
"_appendElementAssumeUniqueAndCapacity","_copyContents","_getElementSlowPath",
"_consumeAndCreateNew","_reserveCapacityAssumingUniqueBuffer",
"_reserveCapacityImpl","_endMutation","reserveCapacity"]
def imports(path):
    lines=pathlib.Path(path).read_text().splitlines()
    return sorted(set(line.strip() for line in lines if line.lstrip().startswith("declare") and (
        "Ts5" in line or any(x in line for x in names))))
a,b=map(imports,sys.argv[1:3])
print("iOS 16.2 compiler imports:",len(a))
print("iOS 17.0 compiler imports:",len(b))
print("Only iOS 17.0:",len(set(b)-set(a)))
pathlib.Path(sys.argv[3]).write_text(json.dumps({"ios16.2":a,"ios17.0":b,
"only17":sorted(set(b)-set(a)),"scope":"Own stock compiler test; no third-party input"},indent=2)+"\n")
