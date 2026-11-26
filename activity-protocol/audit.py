#!/usr/bin/env python3
"""Check exact IR evidence of inheritance and independent nominal identity.

No native aliases, no witness table rewriting and no registration are performed.
"""
import json,pathlib,re,sys
stock,candidate=[pathlib.Path(p).read_text() for p in sys.argv[1:3]]
native="$s10AppIntents18LiveActivityIntentMp"
native_base="$s10AppIntents18LiveActivityIntentPAA06SystemE0Tb"
system="$s10AppIntents12SystemIntentMp"
if native not in stock or native_base not in stock or system not in stock:
    raise SystemExit("Missing native stock protocol/base evidence")
if native in candidate or native_base in candidate:
    raise SystemExit("Unexpected native LiveActivityIntent dependency in local candidate")
defs=[line for line in candidate.splitlines() if line.startswith('@"$s') and "CompatLiveActivityIntentMp" in line and " = " in line]
base=[line for line in candidate.splitlines() if line.startswith('@"$s') and "CompatLiveActivityIntentP" in line and "Tb" in line and " = " in line]
if len(defs)!=1 or len(base)!=1 or system not in candidate:
    raise SystemExit("Expected local protocol and inherited SystemIntent evidence: "+repr((len(defs),len(base))))
# Record names only; no SDK bodies or binaries are copied into public research.
report={"stock_protocol":native,"stock_base":native_base,
        "local_protocol":defs[0].split('"')[1],"local_base":base[0].split('"')[1],
        "shared_base_reference":system,"status":"STRUCTURAL_RESEARCH_ONLY",
        "limitations":["Nominal identity differs","Native AppIntent base witness layout differs across OS versions",
                       "No proof of system intent registration or native protocol substitution"]}
print(json.dumps(report,indent=2))
pathlib.Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+"\n")
