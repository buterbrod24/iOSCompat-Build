"""Version-qualified diagnostic interpretation of supplied Swift witness flags."""
FLAGS={"non_pod":0x10000,"non_inline":0x20000,"spare_bits":0x80000,
       "non_bitwise_takable":0x100000,"enum_witnesses":0x200000,"incomplete":0x400000}

def decode(word,version):
    if type(word) is not int or not 0<=word<=0xffffffff:
        raise ValueError("expected uint32")
    if version not in ("5.7","5.9"):
        raise ValueError("unsupported source version")
    known=FLAGS.copy()
    if version=="5.9":
        known["noncopyable"]=0x800000
    mask=0xff
    for bit in known.values(): mask|=bit
    alignment=(word&0xff)+1
    return {"version":version,"raw":word,"alignment":alignment,
            "alignment_power_of_two":not bool(alignment&(alignment-1)),
            "flags":{name:bool(word&bit) for name,bit in known.items()},
            "unknown_bits":word&~mask,
            "scope":"Supplied flag word only. No native pointer access or compatibility verdict."}
