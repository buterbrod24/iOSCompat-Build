#!/usr/bin/env python3
"""Verify compiler-generated protocol and base requirement descriptors by demangling.

No native aliases, witness rewriting or system registration.
"""
import json,pathlib,re,subprocess,sys
stock,candidate=[pathlib.Path(p).read_text() for p in sys.argv[1:3]]
native="$s10AppIntents18LiveActivityIntentMp"
native_base="$s10AppIntents18LiveActivityIntentPAA06SystemE0Tb"
system="$s10AppIntents12SystemIntentMp"
if not all(s in stock for s in (native,native_base,system)):
    raise SystemExit("Missing native stock protocol/base evidence")
if native in candidate or native_base in candidate:
    raise SystemExit("Unexpected native LiveActivityIntent dependency in local candidate")
names=sorted(set(re.findall(r'@"(\$s[^"]+(?:Mp|Tb))"',candidate)))
defined=set(re.findall(r'^@"(\$s[^"]+)"[ \t]*=[ \t]*(?![ \t]|external\b)',candidate,re.M))
def demangle(name):
    return subprocess.check_output(["xcrun","swift-demangle","--compact",name],text=True).strip()
decoded={n:demangle(n) for n in names}
owner="ActivityCompatResearch.CompatLiveActivityIntent"
for n,label in decoded.items():
    print(n,label,"defined" if n in defined else "reference")
protocols=[n for n,label in decoded.items() if n in defined and label=="protocol descriptor for "+owner]
bases=[n for n,label in decoded.items() if n in defined and label == "base conformance descriptor for "+owner+": AppIntents.SystemIntent"]
if len(protocols)!=1 or len(bases)!=1 or system not in candidate:
    raise SystemExit("Expected one protocol and one base descriptor: "+repr((protocols,bases)))
report={"stock_protocol":native,"stock_base":native_base,
        "local_protocol":protocols[0],"local_base":bases[0],
        "shared_base_reference":system,"status":"STRUCTURAL_RESEARCH_ONLY",
        "limitations":["Nominal identity differs","Native AppIntent base witness layout differs across OS versions",
                       "No proof of system intent registration or native protocol substitution"]}
print(json.dumps(report,indent=2))
pathlib.Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+"\n")
