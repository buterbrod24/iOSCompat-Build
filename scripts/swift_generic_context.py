"""Fixed generic value-type context prefix, Swift 5.9; no pointer interpretation."""
import struct
from collections import Counter

REQUIREMENTS={0:"protocol",1:"same_type",2:"base_class",3:"same_conformance",4:"same_shape",31:"layout"}

def inspect_generic(data,pos,end):
    # Struct/enum: common nominal prefix 20 + two 32-bit fields;
    # then type generic header: two relative pointers + four uint16 fields.
    if pos<0 or end>len(data) or end-pos<44:
        return {"status":"truncated_generic_header"}
    nparams,nreq,nkeys,flags=struct.unpack_from("<4H",data,pos+36)
    info={"parameters":nparams,"requirements":nreq,"key_arguments":nkeys,"flags":flags,
          "nonzero_legacy_extra_field":bool(flags),"type_pack_flag":bool(flags&1)}
    if flags&~1:
        return {"status":"unknown_generic_flags",**info}
    # Fixed arrays only; do not read pack shape data or other trailing objects.
    param_start=pos+44
    req_start=(param_start+nparams+3)&~3
    if nparams>4096 or nreq>4096:
        return {"status":"array_budget_exceeded",**info}
    if req_start+12*nreq>end:
        return {"status":"truncated_generic_arrays",**info}
    params=Counter()
    reqs=Counter()
    key_params=0
    key_requirements=0
    pack_requirements=0
    for v in data[param_start:param_start+nparams]:
        kind=v&63
        if v&64 or kind>1:
            return {"status":"unknown_parameter_descriptor",**info}
        params["type" if kind==0 else "type_pack"]+=1
        key_params+=bool(v&128)
    for i in range(nreq):
        v=struct.unpack_from("<I",data,req_start+12*i)[0]
        if v&~0xbf or (v&31) not in REQUIREMENTS:
            return {"status":"unknown_requirement_descriptor",**info}
        reqs[REQUIREMENTS[v&31]]+=1
        key_requirements+=bool(v&128)
        pack_requirements+=bool(v&32)
    return {"status":"fixed_arrays_observed",**info,
            "parameter_kinds":dict(sorted(params.items())),
            "requirement_kinds":dict(sorted(reqs.items())),
            "key_parameter_descriptors":key_params,
            "key_requirement_descriptors":key_requirements,
            "pack_requirements":pack_requirements}
