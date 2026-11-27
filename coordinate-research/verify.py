import pathlib,sys
d=pathlib.Path(sys.argv[1])
stock=set((d/"Stock.imports.txt").read_text().splitlines())
adapter=set((d/"Adapter.imports.txt").read_text().splitlines())
expected={
    "_$s7SwiftUI13GeometryProxyV5frame2inSo6CGRectVx_tAA23CoordinateSpaceProtocolRzlF",
    "_$s7SwiftUI4ViewPAAE15coordinateSpaceyQrAA015NamedCoordinateE0VF",
    "_$s7SwiftUI4ViewPAAE15coordinateSpaceyQrAA015NamedCoordinateE0VFQOMQ",
}
missing=expected-stock
if missing: raise SystemExit("Stock evidence missing: "+repr(sorted(missing)))
unexpected=[n for n in adapter if n.startswith("_$s7SwiftUI") and
            any(x in n for x in ("CoordinateSpaceProtocol","NamedCoordinateSpace","LocalCoordinateSpace","GlobalCoordinateSpace","015NamedCoordinateE0"))]
if unexpected: raise SystemExit("Legacy adapter imported modern coordinate types: "+repr(unexpected))
print("PASS stock function and opaque descriptor evidence")
print("PASS independent legacy adapter has no identified modern coordinate imports")
print("NOTE: independent types; no ABI identity or layout equivalence")
