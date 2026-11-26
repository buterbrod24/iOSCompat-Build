#!/usr/bin/env python3
"""Redirect only selected SDK imports in self-authored independent clients."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import probe_rebind
from macho_imports import read_imports
configs={
 "streams": (b"/usr/lib/swift/libswift_Concurrency.dylib",b"@rpath/libConcurrencyCompat.dylib",{
    "_$sScS10makeStream2of15bufferingPolicyScSyxG6stream_ScS12ContinuationVyx_G12continuationtxm_AG09BufferingE0Oyx__GtFZ",
    "_$sScs10makeStream2of8throwing15bufferingPolicyScsyxs5Error_pG6stream_Scs12ContinuationVyxsAE_p_G12continuationtxm_sAE_pmAI09BufferingF0OyxsAE_p__GtsAE_pRs_rlFZ"}),
 "toolbar": (b"/System/Library/Frameworks/SwiftUI.framework/SwiftUI",b"@rpath/libSwiftUICompat.dylib",{
    "_$s7SwiftUI20ToolbarItemPlacementV13topBarLeadingACvgZ"})
}
kind,p=sys.argv[1:3]
p=pathlib.Path(p);before=p.read_bytes()
provider,replacement,targets=configs[kind]
probe_rebind.UIKIT=provider;probe_rebind.OVERLAY=replacement
rows,_,complete=read_imports(before)
hits=[r for r in rows if r[3]=="chained" and r[0] in targets]
if not complete or {r[0] for r in hits}!=targets or len(hits)!=len(targets) or len({r[1] for r in hits})!=1:
    raise SystemExit("Unexpected independent client imports "+repr(hits))
after,report=probe_rebind.rebind(before,{n.encode() for n in targets},len(targets))
newrows,_,ok=read_imports(after)
expected={(n,report["new_ordinal"] if o==report["old_ordinal"] and n in targets else o,w,s) for n,o,w,s in rows}
if not ok or set(newrows)!=expected:
    raise SystemExit("Unexpected import change")
p.write_bytes(after)
print(kind,"verified exact rebind:",report)
