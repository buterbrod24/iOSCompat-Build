"""Fixed generic value-type context prefix, Swift 5.9; no pointer interpretation."""
import struct
from collections import Counter

REQUIREMENTS={0:"protocol",1:"same_type",2:"base_class",3:"same_conformance",4:"same_shape",31:"layout"}

def inspect_pack_shapes(data,start,end,nkeys,metadata_count,witness_count):
    """Check declared shape-array invariants without interpreting argument pointers."""
    if start<0 or end>len(data) or start+4>end:
        return {"status":"truncated_pack_header"}
    count,classes=struct.unpack_from("<2H",data,start)
    info={"packs":count,"shape_classes":classes}
    if count>8192 or start+4+8*count>end:
        return {"status":"truncated_or_oversized_pack_array",**info}
    if count!=metadata_count+witness_count:
        return {"status":"pack_count_mismatch",**info}
    if classes>count or (count and not classes) or classes>nkeys:
        return {"status":"invalid_shape_class_count",**info}
    kinds=Counter()
    indices=set()
    used_classes=set()
    last=(-1,-1)
    nonzero_unused=0
    for i in range(count):
        kind,index,shape,unused=struct.unpack_from("<4H",data,start+4+8*i)
        if kind not in (0,1):
            return {"status":"unknown_pack_kind",**info}
        if (kind,index)<=last or index in indices:
            return {"status":"unordered_or_duplicate_pack_index",**info}
        if index>=nkeys or index<classes or shape>=classes:
            return {"status":"pack_index_or_shape_out_of_range",**info}
        last=(kind,index)
        indices.add(index)
        used_classes.add(shape)
        kinds["metadata" if kind==0 else "witness_table"]+=1
        nonzero_unused+=bool(unused)
    if kinds["metadata"]!=metadata_count or kinds["witness_table"]!=witness_count:
        return {"status":"pack_kind_count_mismatch",**info}
    if len(used_classes)!=classes:
        return {"status":"unrepresented_shape_classes",**info}
    return {"status":"shape_array_observed",**info,"kinds":dict(sorted(kinds.items())),
            "nonzero_unused_fields":nonzero_unused}

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
    # Fixed arrays and optional pack shapes; no pointer-field interpretation.
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
    keyed_metadata_packs=0
    keyed_witness_packs=0
    for v in data[param_start:param_start+nparams]:
        kind=v&63
        if v&64 or kind>1:
            return {"status":"unknown_parameter_descriptor",**info}
        params["type" if kind==0 else "type_pack"]+=1
        key_params+=bool(v&128)
        keyed_metadata_packs+=int(kind==1 and bool(v&128))
    for i in range(nreq):
        v=struct.unpack_from("<I",data,req_start+12*i)[0]
        if v&~0xbf or (v&31) not in REQUIREMENTS:
            return {"status":"unknown_requirement_descriptor",**info}
        reqs[REQUIREMENTS[v&31]]+=1
        key_requirements+=bool(v&128)
        pack_requirements+=bool(v&32)
        keyed_witness_packs+=int((v&0xa0)==0xa0)
    if flags&1:
        shapes=inspect_pack_shapes(data,req_start+12*nreq,end,nkeys,keyed_metadata_packs,keyed_witness_packs)
    else:
        shapes={"status":"pack_markers_without_header_flag" if params["type_pack"] or pack_requirements else "not_declared"}
    return {"status":"fixed_arrays_observed",**info,
            "parameter_kinds":dict(sorted(params.items())),
            "requirement_kinds":dict(sorted(reqs.items())),
            "key_parameter_descriptors":key_params,
            "key_requirement_descriptors":key_requirements,
            "pack_requirements":pack_requirements,"pack_shapes":shapes}
