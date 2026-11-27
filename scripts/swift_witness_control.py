"""Bounded Swift 5.9 conformance trailing-header observations, never resolve pointers."""
import struct

def inspect_witness_control(data,pos,end,flags):
    if pos<0 or end>len(data) or end-pos<16:
        return {"status":"truncated_conformance_prefix"}
    conditional=(flags>>8)&255
    packs=(flags>>24)&255
    retroactive=bool(flags&64)
    resilient=bool(flags&65536)
    generic=bool(flags&131072)
    # Skip known fixed arrays. The fields are not interpreted.
    cursor=pos+16+4*retroactive+12*conditional+8*packs
    if cursor>end:
        return {"status":"truncated_preceding_arrays"}
    info={"conditional_requirements":conditional,"conditional_pack_descriptors":packs}
    if resilient:
        if cursor+4>end:
            return {"status":"truncated_resilient_header",**info}
        count=struct.unpack_from("<I",data,cursor)[0]
        if count>65536 or cursor+4+8*count>end:
            return {"status":"truncated_or_oversized_resilient_array",**info}
        info["resilient_witness_records"]=count
        cursor+=4+8*count
    if generic:
        if cursor+12>end:
            return {"status":"truncated_generic_witness_control",**info}
        size,private_and_flag,instantiator,private_data=struct.unpack_from("<HHII",data,cursor)
        info["generic_witness_control"]={"template_words":size,
            "private_words":private_and_flag>>1,
            "requires_instantiation_bit":bool(private_and_flag&1),
            "instantiator_field_nonzero":bool(instantiator),
            "private_data_field_nonzero":bool(private_data)}
    return {"status":"trailing_headers_observed",**info}
