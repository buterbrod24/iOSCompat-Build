#!/usr/bin/env python3
"""Read-only inventory of thin Mach-O imports inside an IPA. Unknown is not compatible."""
import argparse, json, pathlib, sys, zipfile, struct
from macho_imports import read_imports

def scan(path, catalog):
    result = {"schema": 1, "target": catalog["target"], "images": [], "limitations": [
        "No dependency resolution or dyld cache export inventory yet",
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
                    image.update(sources=sources, complete=complete, imports=[])
                    for name, ordinal, weak, source in rows:
                        key = name[1:] if name.startswith("_") else name
                        entry = catalog["symbols"].get(key, {})
                        image["imports"].append(dict(symbol=name, ordinal=ordinal, weak=weak, source=source,
                            status=entry.get("status", "unknown"), expected_provider=entry.get("provider")))
                except (ValueError, struct.error, OSError) as exc:
                    image["error"] = str(exc)
    return result

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
