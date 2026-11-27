#!/usr/bin/env python3
"""Read-only inventory of thin Mach-O imports inside an IPA. Unknown is not compatible."""
import argparse, json, pathlib, sys, zipfile, struct, posixpath
from import_summary import summarize
from backdeploy_markers import inspect_markers, annotate_imports
from macho_imports import read_imports, read_dependencies, declared_provider

def validate_inventory(inventory, target):
    if inventory.get("schema") != 1 or inventory.get("target") != target:
        raise ValueError("inventory schema or target mismatch")
    if inventory.get("architecture") != "arm64":
        raise ValueError("inventory architecture must be arm64")
    if not isinstance(inventory.get("build"), str) or not inventory["build"]:
        raise ValueError("inventory build required")
    if not isinstance(inventory.get("providers"), dict):
        raise ValueError("inventory providers required")
    for path, record in inventory["providers"].items():
        if not path.startswith(("/usr/lib/", "/System/Library/")):
            raise ValueError("invalid system provider")
        if not isinstance(record.get("symbols"), dict):
            raise ValueError("invalid symbols")
        if any(value not in ("present", "absent") for value in record["symbols"].values()):
            raise ValueError("invalid symbol observation")

def export_evidence(inventory, provider, symbol):
    # Sparse observations only: no negative inference from missing entries.
    if inventory is None or provider is None:
        return "unknown"
    return inventory["providers"].get(provider, {}).get("symbols", {}).get(symbol, "unknown")

def scan(path, catalog, inventory=None):
    if inventory is not None:
        validate_inventory(inventory, catalog["target"])
    result = {"schema": 7, "target": catalog["target"], "images": [], "limitations": [
        "Local path candidates only; no inherited runpath stack, executable context or dyld cache export inventory",
        "Fat binaries and classical bind streams are not fully decoded",
        "Candidate evidence is not proof of compatibility with this image",
        "Back-deployment markers are syntactic nlist name evidence only; stripped and inlined code may be invisible"]}
    with zipfile.ZipFile(path) as archive:
        budget = 1024 * 1024 * 1024
        for info in archive.infolist():
            if info.is_dir() or not info.filename.startswith("Payload/"):
                continue
            with archive.open(info) as f:
                magic = f.read(4)
                if magic not in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf", b"\xbe\xba\xfe\xca", b"\xbf\xba\xfe\xca"):
                    continue
                image = {"path": info.filename}
                result["images"].append(image)
                if magic != b"\xcf\xfa\xed\xfe":
                    image["error"] = "unsupported universal binary"
                    continue
                if info.file_size > 256 * 1024 * 1024 or info.file_size > budget:
                    image["error"] = "size budget exceeded"
                    continue
                budget -= info.file_size
                try:
                    data = magic + f.read()
                    rows, sources, complete = read_imports(data)
                    deps, rpaths = read_dependencies(data)
                    cpu, subtype = struct.unpack_from('<II', data, 4)
                    image.update(sources=sources, complete=complete, imports=[], dependencies=deps, rpaths=rpaths, cpu_type=cpu, cpu_subtype=subtype)
                    for name, ordinal, weak, source in rows:
                        key = name[1:] if name.startswith("_") else name
                        entry = catalog["symbols"].get(key, {})
                        provider = declared_provider(deps, ordinal, source)
                        matched = bool(entry) and provider == entry.get("provider")
                        library_weak = provider is not None and 1 <= ordinal <= len(deps) and deps[ordinal-1]["kind"] == "weak"
                        image["imports"].append(dict(symbol=name, ordinal=ordinal, weak=weak, source=source,
                            declared_provider=provider, catalog_provider_match=matched,
                            library_weak=library_weak, effective_weak=bool(weak or library_weak),
                            native_export=export_evidence(inventory, provider, key) if cpu == 0x100000c and subtype & 0xffffff == 0 else "unknown",
                            status=entry["status"] if matched else "unknown", expected_provider=entry.get("provider")))
                    image["backdeploy"] = inspect_markers(data)
                    annotate_imports(image)
                except (ValueError, struct.error, OSError) as exc:
                    image["error"] = str(exc)
    if inventory is not None:
        result["inventory_build"] = inventory["build"]
    map_dependencies(result["images"])
    result["research_queue"] = summarize(result["images"])
    return result

def map_dependencies(images):
    """Conservative local candidates, never a claim of dyld resolution."""
    index = {image["path"] for image in images}
    def local_path(base, suffix):
        path = posixpath.normpath(posixpath.join(base, suffix))
        return path if path.startswith("Payload/") and path in index else None
    for image in images:
        base = posixpath.dirname(image["path"])
        for dep in image.get("dependencies", []):
            path = dep["path"]
            candidates = set()
            if path.startswith("@loader_path/"):
                candidate = local_path(base, path[len("@loader_path/"):])
                if candidate: candidates.add(candidate)
            elif path.startswith("@rpath/"):
                for rpath in image.get("rpaths", []):
                    if rpath == "@loader_path" or rpath.startswith("@loader_path/"):
                        root = posixpath.join(base, rpath[len("@loader_path"):].lstrip("/"))
                        candidate = local_path(root, path[len("@rpath/"):])
                        if candidate: candidates.add(candidate)
            dep["local_candidates"] = sorted(candidates)
            if path.startswith(("/System/Library/", "/usr/lib/")):
                dep["resolution"] = "system_unverified"
            elif len(candidates) == 1:
                dep["resolution"] = "local_candidate"
            elif candidates:
                dep["resolution"] = "ambiguous_local_candidates"
            else:
                dep["resolution"] = "unresolved_context"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--inventory", type=pathlib.Path, help="Local sparse system export observations JSON")
    args = parser.parse_args()
    if args.ipa.resolve() == args.output.resolve():
        parser.error("output must not overwrite input")
    catalog = json.loads((pathlib.Path(__file__).parent / "compat_catalog.json").read_text())
    inventory = json.loads(args.inventory.read_text()) if args.inventory else None
    report = scan(args.ipa, catalog, inventory)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("Images:", len(report["images"]), "; report saved locally")
    for key, count in sorted(report["research_queue"]["counts"].items()):
        print(key, count)
if __name__ == "__main__":
    main()
