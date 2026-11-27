"""Audit new diagnostic images; old stock clients are inventoried, not gated."""
import pathlib
import re
import sys
import json

BLOCKED = {
    "swift_conformsToProtocol2",
    "swift_getOpaqueTypeMetadata2",
    "swift_getOpaqueTypeConformance2",
    "swift_getTypeByMangledNameInContext2",
    "swift_getTypeByMangledNameInContextInMetadataState2",
}
CLIENTS = {
    "libUnified_witness_Client.dylib": "libWitnessFixture.dylib",
    "libUnified_opaque_Client.dylib": "libOpaqueFixture.dylib",
    "libUnified_mutation_Client.dylib": "libSwiftCoreMutationCompat.dylib",
}
GATED = {"UnifiedProbe", *CLIENTS, *CLIENTS.values()}
SYMBOL = re.compile(r"(?<![A-Za-z0-9_$])_?(swift_[A-Za-z0-9_]+)(?![A-Za-z0-9_$])")

def blocked_symbols(text):
    return sorted(set(SYMBOL.findall(text)) & BLOCKED)

def dependencies(text):
    # otool -L first line is image filename; subsequent rows are install names.
    return [line.strip().split(" (compatibility version", 1)[0]
            for line in text.splitlines()[1:] if line.strip()]

def audit(root):
    errors = []
    report = {}
    for p in sorted(root.glob("*.imports.txt")):
        name = p.name.removesuffix(".imports.txt")
        deps = dependencies((root / (name + ".dependencies.txt")).read_text())
        blocked = blocked_symbols(p.read_text())
        report[name] = {"blocked_imports": blocked, "dependencies": deps,
                        "gated": name in GATED}
        if name in GATED and blocked:
            errors.append(name + ": forbidden imports " + ", ".join(blocked))
        if name in CLIENTS and "@rpath/" + CLIENTS[name] not in deps:
            errors.append(name + ": missing independent fixture dependency")
        if name == "UnifiedProbe":
            for dep in deps:
                if pathlib.PurePosixPath(dep).name in GATED - {"UnifiedProbe"}:
                    errors.append(name + ": eager diagnostic dependency " + dep)
    missing = GATED - report.keys()
    if missing:
        errors.append("missing audit images: " + ", ".join(sorted(missing)))
    if len(report) != 16:
        errors.append("expected 16 Mach-O images, found " + str(len(report)))
    return {"images": report, "errors": errors}

if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1])
    result = audit(root)
    (root / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    sys.exit(bool(result["errors"]))
