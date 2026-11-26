#!/usr/bin/env python3
"""Compare public upstream runtime ABI declarations, never generate replacement code."""
import pathlib,re,sys
source=pathlib.Path(sys.argv[1]).read_text()
names=["swift_conformsToProtocol","swift_getOpaqueTypeMetadata","swift_getOpaqueTypeConformance","swift_getTypeByMangledNameInContext","swift_getTypeByMangledNameInContextInMetadataState"]
for name in names:
    old=re.search(r'FUNCTION\(\s*\w+\s*,\s*\w+\s*,\s*'+re.escape(name)+r'\s*,(.*?)\n\s*(?:FUNCTION|//|#)',source,re.S)
    new=re.search(r'FUNCTION\(\s*\w+\s*,\s*\w+\s*,\s*'+re.escape(name)+r'2\s*,(.*?)\n\s*(?:FUNCTION|//|#)',source,re.S)
    print(name)
    for label,match in [("legacy",old),("new",new)]:
        if not match:
            print("  "+label+": no declaration found"); continue
        s=match.group(1)
        args=re.search(r'ARGS\(([^)]*)\)',s)
        returns=re.search(r'RETURNS\(([^)]*)\)',s)
        prefix=s.split("RETURNS")[0].strip().rstrip(",").replace("\n"," ")
        print("  "+label+": "+prefix+"; args="+(args.group(1) if args else "?")+"; returns="+(returns.group(1) if returns else "?"))
    print("  BLOCKED: investigate descriptor/witness pointer signing and old runtime semantics")
