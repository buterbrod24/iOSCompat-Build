"""Summarize observed import evidence, never certify app compatibility."""
from collections import Counter

def summarize(images):
    groups = {}
    incomplete = []
    for image in images:
        path = image["path"]
        if image.get("error") or not image.get("complete", False):
            incomplete.append(path)
        # Only known ordinary ARM64 images participate in target evidence.
        applicable = image.get("cpu_type") == 0x100000c and image.get("cpu_subtype", -1) & 0xffffff == 0
        for row in image.get("imports", []):
            provider = row.get("declared_provider")
            key = (provider, row["symbol"], applicable)
            item = groups.setdefault(key, {"provider":provider,"symbol":row["symbol"],
                "target_architecture_match":applicable,"images":set(),"required":False,
                "observations":set(),"catalog_statuses":set()})
            item["images"].add(path)
            item["required"] |= not (row.get("weak", False) or row.get("library_weak", False))
            item["observations"].add(row.get("native_export","unknown") if applicable else "unknown")
            item["catalog_statuses"].add(row.get("status","unknown") if applicable and row.get("catalog_provider_match") else "unknown")
    rows = []
    for item in groups.values():
        native = item["observations"] - {"unknown"}
        catalog = item["catalog_statuses"] - {"unknown"}
        if not item["target_architecture_match"]:
            action = "architecture_unverified"
        elif len(native)>1 or len(catalog)>1 or ("present" in native and "missing_unresolved" in catalog):
            action = "conflicting_evidence"
        elif "present" in native:
            action = "native_lookup_present"
        elif "candidate_independent_device_tested" in catalog:
            action = "review_independent_device_tested_candidate"
        elif "candidate_internal_device_tested_stock_linked" in catalog:
            action = "verify_independent_device_execution"
        elif "candidate_device_tested" in catalog:
            action = "review_tested_candidate"
        elif "absent" in native or "missing_unresolved" in catalog:
            action = "investigate_required_absence" if item["required"] else "investigate_weak_absence"
        else:
            action = "unknown"
        item["action"] = action
        for field in ("images","observations","catalog_statuses"):
            item[field] = sorted(item[field])
        rows.append(item)
    order = {"conflicting_evidence":0,"investigate_required_absence":1,"review_tested_candidate":2,"review_independent_device_tested_candidate":2,"verify_independent_device_execution":2,
             "investigate_weak_absence":3,"architecture_unverified":4,"unknown":5,"native_lookup_present":6}
    rows.sort(key=lambda x:(order[x["action"]],x["provider"] or "",x["symbol"],x["target_architecture_match"]))
    return {"unique_import_groups":len(rows),"counts":dict(Counter(x["action"] for x in rows)),
            "incomplete_images":sorted(set(incomplete)),"items":rows,
            "note":"Research queue only; import strength, lookup scope, reexports and runtime behavior need verification."}
