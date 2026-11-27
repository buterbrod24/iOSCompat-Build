import pathlib,sys
d=pathlib.Path(sys.argv[1])
stock=set((d/"Stock.imports.txt").read_text().splitlines())
adapter=set((d/"Adapter.imports.txt").read_text().splitlines())
expected={
    "_$s7SwiftUI10TransitionPAAE8combined4withQrqd___tAaBRd__lF",
    "_$s7SwiftUI10TransitionPAAE8combined4withQrqd___tAaBRd__lFQOMQ",
    "_$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgF",
    "_$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgFQOMQ",
    "_$s7SwiftUI13AnyTransitionVyACxcAA0D0RzlufC",
}
for n in sorted(expected): print(("OBSERVED " if n in stock else "NOT_OBSERVED ")+n)
if not expected <= stock: raise SystemExit("Stock import evidence incomplete")
if adapter & expected: raise SystemExit("Legacy adapter unexpectedly imports modern transition API")
for n in sorted(adapter):
    if n.startswith("_$s7SwiftUI") and any(k in n for k in ("IdentityTransition","OpacityTransition","MoveTransition","OffsetTransition","10TransitionP")):
        raise SystemExit("Modern transition import: "+n)
print("PASS stock function and descriptor import evidence")
print("PASS legacy import gate")
print("NOTE: independent wrapper; no ABI layout or rendering parity claim")
