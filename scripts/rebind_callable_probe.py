#!/usr/bin/env python3
"""Only independent SDK client, never third-party app binaries."""
import pathlib,sys,struct
from macho_imports import read_imports
import probe_rebind
p=pathlib.Path(sys.argv[1])
before=p.read_bytes()
target="_$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSSYttcAA0A6IntentRzlufC"
default="_$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ"
rows,_,complete=read_imports(before)
hits=[r for r in rows if r[3]=="chained" and r[0] in (target,default)]
if not complete or len([r for r in hits if r[0]==target])!=1 or len(hits)>2:
    raise SystemExit("Unexpected independent SDK imports: "+repr(hits))
if len({r[1] for r in hits})!=1: raise SystemExit("Inconsistent original provider")
symbols={r[0].encode() for r in hits}
after,report=probe_rebind.rebind(before,symbols,len(hits))
newrows,_,ok=read_imports(after)
expected={(n,report["new_ordinal"] if o==report["old_ordinal"] and n.encode() in symbols else o,w,s) for n,o,w,s in rows}
if not ok or set(newrows)!=expected:
    raise SystemExit("Unexpected import change")
p.write_bytes(after)
print("Rebound exact callable imports, preserved weak bits and all other decoded imports:",report)
