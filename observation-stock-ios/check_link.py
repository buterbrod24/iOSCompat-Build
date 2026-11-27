"""Verify independent object requirements and direct linked providers, not runtime behavior."""
import pathlib,re,sys

imports,exports,bindings=(pathlib.Path(p).read_text().splitlines() for p in sys.argv[1:4])
required=set(pathlib.Path("observation-research/required-exports.txt").read_text().splitlines())
observed={s for s in imports if s.startswith("_$s11Observation")}
bound={}
for row in bindings:
    m=re.search(r"(_\$s11Observation\S+)\s+\(from ([^)]+)\)",row)
    if m:
        bound.setdefault(m[1],set()).add(m[2])
missing=observed-set(exports)
wrong={s for s in observed if bound.get(s)!={"libObservationResearch"}}
for s in sorted(observed):
    print("MATCH" if s not in missing|wrong else "UNVERIFIED",s)
print("Original eight required names exercised:",len(required & observed),"/",len(required))
print("Independent object imports verified:",len(observed-(missing|wrong)),"/",len(observed))
print("Static link audit only; client has not run on iOS.")
if not required.issubset(observed) or missing or wrong:
    raise SystemExit("incomplete coverage or provider mismatch")
