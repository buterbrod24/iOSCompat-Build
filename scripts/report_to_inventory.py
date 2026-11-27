#!/usr/bin/env python3
"""Convert explicitly scoped Unified Probe 0.6.0 dlsym observations to sparse inventory."""
import argparse, json, pathlib, re
from analyze_ipa import validate_inventory

BLOCKS = {
    "Swift Core / runtime export evidence": "/usr/lib/swift/libswiftCore.dylib",
    "Concurrency / executor and stream exports": "/usr/lib/swift/libswift_Concurrency.dylib",
    "SwiftUI / protocol export evidence": "/System/Library/Frameworks/SwiftUI.framework/SwiftUI",
}

# Exact query allowlist taken from Unified Probe 0.6.0 Suites.swift.
EXPECTED = dict(zip(BLOCKS, [
    [
        "swift_conformsToProtocol",
        "swift_conformsToProtocol2",
        "swift_getOpaqueTypeMetadata",
        "swift_getOpaqueTypeMetadata2",
        "swift_getOpaqueTypeConformance",
        "swift_getOpaqueTypeConformance2",
        "swift_getTypeByMangledNameInContext",
        "swift_getTypeByMangledNameInContext2",
        "swift_getTypeByMangledNameInContextInMetadataState",
        "swift_getTypeByMangledNameInContextInMetadataState2"
    ],
    [
        "$sScF7enqueueyys11ExecutorJobVnFTq",
        "$sScF7enqueueyys3JobVnFTq",
        "$sScf7enqueueyys11ExecutorJobVnFTq",
        "$sScf7enqueueyys3JobVnFTq",
        "$sScS10makeStream2of15bufferingPolicyScSyxG6stream_ScS12ContinuationVyx_G12continuationtxm_AG09BufferingE0Oyx__GtFZ"
    ],
    [
        "$s7SwiftUI4ViewMp",
        "$s7SwiftUI10ShapeStyleMp",
        "$s7SwiftUI6LayoutMp",
        "$s7SwiftUI10ShapeStyleP7resolve2in8ResolvedQzAA17EnvironmentValuesV_tFTq",
        "$s7SwiftUI19UIViewRepresentableP14_layoutOptionsyAA013_PlatformViewd6LayoutF0V0C4TypeQzFZTq",
        "$s7SwiftUI29UIViewControllerRepresentableP14_layoutOptionsyAA013_PlatformViewe6LayoutG0V0cD4TypeQzFZTq"
    ]
]))

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
    expected = {BLOCKS[k]:set(names) for k,names in EXPECTED.items()}
    if set(providers) != set(expected) or any(set(providers[p]["symbols"]) != names for p,names in expected.items()):
        raise ValueError("unexpected observation coverage")
    inventory = {"schema":1,"target":"16.2","build":"20C65","architecture":"arm64",
                 "method":"Unified Probe 0.6.0 dlsym using named dlopen handle without RTLD_FIRST; dependency lookup possible; architecture from probe build target",
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
