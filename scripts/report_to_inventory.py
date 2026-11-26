#!/usr/bin/env python3
"""Convert explicitly scoped Unified Probe 0.6.0 dlsym observations to sparse inventory."""
import argparse, json, pathlib, re
from analyze_ipa import validate_inventory

BLOCKS = {
    "Swift Core / runtime export evidence": "/usr/lib/swift/libswiftCore.dylib",
    "Concurrency / executor and stream exports": "/usr/lib/swift/libswift_Concurrency.dylib",
    "SwiftUI / protocol export evidence": "/System/Library/Frameworks/SwiftUI.framework/SwiftUI",
}

def convert(text):
    lines = text.splitlines()
    if lines[:2] != ["iOSCompat Unified Probe 0.6.0", "OS: 16.2"]:
        raise ValueError("unsupported report version or OS")
    if len(lines) < 3 or lines[2] != "Completed 42/42; PASS 38; FAIL 0; EVIDENCE 4; INTERRUPTED 0":
        raise ValueError("expected completed clean 0.6.0 report")
    if "OS: Version 16.2 (Build 20C65)" not in lines:
        raise ValueError("expected build 20C65")
    providers = {}
    active = None
    for line in lines[3:]:
        if line.startswith("START "):
            active = None
        elif line.startswith("EVIDENCE "):
            active = BLOCKS.get(line[len("EVIDENCE "):])
            if active:
                if active in providers:
                    raise ValueError("duplicate observation block")
                providers[active] = {"symbols":{}}
        elif active:
            match = re.fullmatch(r"(PRESENT|ABSENT) ([^\s]+)", line)
            if match:
                state, symbol = match.groups()
                symbols = providers[active]["symbols"]
                if symbol in symbols:
                    raise ValueError("duplicate observation")
                symbols[symbol] = state.lower()
    counts = {BLOCKS[k]: n for k,n in zip(BLOCKS,(10,5,6))}
    if set(providers) != set(counts) or any(len(providers[p]["symbols"]) != n for p,n in counts.items()):
        raise ValueError("unexpected observation coverage")
    inventory = {"schema":1,"target":"16.2","build":"20C65","architecture":"arm64",
                 "method":"Unified Probe 0.6.0 provider-scoped dlsym; architecture from probe build target",
                 "providers":providers}
    validate_inventory(inventory,"16.2")
    return inventory

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report",type=pathlib.Path)
    parser.add_argument("--output",required=True,type=pathlib.Path)
    args = parser.parse_args()
    inventory = convert(args.report.read_text(encoding="utf-8-sig"))
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(inventory,f,indent=2)
    print("Saved",sum(len(p["symbols"]) for p in inventory["providers"].values()),"observations locally")

if __name__ == "__main__":
    main()
