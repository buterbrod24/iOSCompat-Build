#!/usr/bin/env python3
"""Read-only inventory of thin Mach-O imports inside an IPA. Unknown is not compatible."""
import argparse, json, pathlib, sys, zipfile, struct, posixpath
from macho_imports import read_imports, read_dependencies, declared_provider

def scan(path, catalog):
    result = {"schema": 3, "target": catalog["target"], "images": [], "limitations": [
        "Local path candidates only; no inherited runpath stack, executable context or dyld cache export inventory",
        "Fat binaries and classical bind streams are not fully decoded",
        "Candidate evidence is not proof of compatibility with this image"]}
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
                    image.update(sources=sources, complete=complete, imports=[], dependencies=deps, rpaths=rpaths)
                    for name, ordinal, weak, source in rows:
                        key = name[1:] if name.startswith("_") else name
                        entry = catalog["symbols"].get(key, {})
                        provider = declared_provider(deps, ordinal, source)
                        matched = bool(entry) and provider == entry.get("provider")
                        image["imports"].append(dict(symbol=name, ordinal=ordinal, weak=weak, source=source,
                            declared_provider=provider, catalog_provider_match=matched,
                            status=entry["status"] if matched else "unknown", expected_provider=entry.get("provider")))
                except (ValueError, struct.error, OSError) as exc:
                    image["error"] = str(exc)
    map_dependencies(result["images"])
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
    args = parser.parse_args()
    if args.ipa.resolve() == args.output.resolve():
        parser.error("output must not overwrite input")
    catalog = json.loads((pathlib.Path(__file__).parent / "compat_catalog.json").read_text())
    report = scan(args.ipa, catalog)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("Images:", len(report["images"]), "; report saved locally")
if __name__ == "__main__":
    main()
