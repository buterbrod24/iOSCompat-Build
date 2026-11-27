"""Opt-in bounded inventory of Swift metadata evidence in a local IPA."""
import struct
from collections import Counter
import swift_descriptor_inventory as nominal
import swift_protocol_inventory as protocols
import swift_typeref_inventory as typeref

CORE="/usr/lib/swift/libswiftCore.dylib"
LAYOUT_NAMES=frozenset((
    "_swift_allocateGenericClassMetadataWithLayoutString",
    "_swift_allocateGenericValueMetadataWithLayoutString",
    "_swift_initStructMetadataWithLayoutString",
    "_swift_generic_instantiateLayoutString",
))

def inspect_image(data):
    result={}
    for name,inspect in (("nominal",nominal.inspect),("protocols",protocols.inspect),("typeref",typeref.inspect)):
        try:
            r=inspect(data)
            # Per-context details may be large. Keep aggregate observations only.
            if name=="nominal" and "generic_value_contexts" in r:
                r["generic_value_contexts"].pop("details",None)
            result[name]=r
        except (ValueError,struct.error,OverflowError) as exc:
            result[name]={"status":"uninspected_error","error":str(exc)}
    return result

def summarize(images):
    counts=Counter()
    layouts=Counter()
    flags=0
    pack_flags=0
    for image in images:
        meta=image.get("swift_metadata")
        if not meta:
            counts["uninspected_image"]+=1
            continue
        for key in ("nominal","protocols","typeref"):
            counts[key+":"+meta.get(key,{}).get("status","uninspected")]+=1
        n=meta.get("nominal",{})
        flags+=n.get("layout_string_flag_headers",0)
        pack_flags+=n.get("generic_value_contexts",{}).get("type_pack_flag",0)
        # Exact provider match; count distinct symbol/image observations, not raw records.
        if image.get("cpu_type")==0x100000c and image.get("cpu_subtype",-1)&0xffffff==0:
            names={r["symbol"] for r in image.get("imports",[]) if r.get("declared_provider")==CORE and r.get("symbol") in LAYOUT_NAMES}
            layouts.update(names)
    return {"inspection_counts":dict(sorted(counts.items())),
            "layout_string_flag_headers":flags,"type_pack_flag_headers":pack_flags,
            "layout_runtime_import_image_counts":dict(sorted(layouts.items())),
            "note":"Observed bounded sections and exact declared imports only. Zero observations are not proof of absence. No pointers followed at runtime, no compatibility verdict."}
