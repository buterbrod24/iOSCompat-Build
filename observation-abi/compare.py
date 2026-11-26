"""Compare exact symbol names only, not type layout or ABI semantics."""
import pathlib,sys
stock,candidate = (set(pathlib.Path(p).read_text().splitlines()) for p in sys.argv[1:3])
required=pathlib.Path("observation-research/required-exports.txt").read_text().splitlines()
observed={s for s in stock if s.startswith("_$s11Observation")}
missing=observed-candidate
for s in sorted(observed):
    print("MISSING" if s in missing else "MATCH",s)
for s in required:
    if s not in observed: print("NOT EXERCISED",s)
print("STOCK IMPORT MATCHES",len(observed-missing),"/",len(observed))
print("AUDIT LIMIT: export names only; no client execution or metadata layout validation")
if not observed or missing or not set(required[:5]).issubset(observed):
    raise SystemExit("incomplete stock callable coverage or missing exports")
