"""Read-only ordinary/lazy dyld binding opcode import evidence; no fixup execution."""
import struct
from export_trie import uleb
from macho_imports import read_dependencies

class UnsupportedBind(ValueError):
    pass

def signed_leb_skip(data,pos):
    for i in range(10):
        if pos>=len(data): raise ValueError("truncated SLEB")
        b=data[pos];pos+=1
        if not b&128:
            if i==9 and b not in (0,127): raise ValueError("SLEB overflow")
            return pos
    raise ValueError("SLEB overflow")

def decode(data,segments,dep_count,lazy=False):
    if len(data)>32*1024*1024: raise ValueError("bind stream exceeds budget")
    pos=0
    ordinal=None
    symbol=None
    weak=False
    segment=None
    offset=0
    kind=1
    rows=set()
    ended=False
    binds=0
    def advance(amount):
        nonlocal offset
        if offset+amount>=1<<64: raise ValueError("bind offset overflow")
        offset+=amount
    def emit(count=1,skip=0):
        nonlocal binds
        if count==0: return
        if segment is None or symbol is None or ordinal is None:
            raise ValueError("incomplete bind state")
        width=8 if kind==1 else 4
        if offset+(count-1)*(8+skip)+width>segments[segment]:
            raise ValueError("bind target outside segment")
        binds+=count
        if binds>5_000_000 or len(rows)>=500000: raise ValueError("bind count exceeds budget")
        rows.add((symbol,ordinal,weak,"legacy_lazy" if lazy else "legacy_bind"))
        advance(count*(8+skip))
    while pos<len(data):
        byte=data[pos];pos+=1
        op,imm=byte&0xf0,byte&15
        if op==0:
            if imm: raise ValueError("invalid DONE opcode")
            ended=True
            if not lazy:
                if any(data[pos:]): raise ValueError("unexpected data after DONE")
                break
            ordinal=symbol=segment=None
            weak=False;offset=0;kind=1
            continue
        ended=False
        if op==0x10:
            ordinal=imm
        elif op==0x20:
            ordinal,pos=uleb(data,pos,len(data))
        elif op==0x30:
            ordinal=imm-16 if imm else 0
            if ordinal not in (0,-1,-2,-3): raise UnsupportedBind("unsupported special ordinal")
        elif op==0x40:
            if imm&~1: raise UnsupportedBind("unsupported import symbol flags")
            stop=data.find(b"\0",pos)
            if stop<0 or stop==pos or stop-pos>8192: raise ValueError("invalid bind symbol")
            symbol=data[pos:stop].decode("utf-8","strict")
            weak=bool(imm&1);pos=stop+1
        elif op==0x50:
            if imm not in (1,2,3): raise UnsupportedBind("unsupported bind type")
            kind=imm
        elif op==0x60:
            pos=signed_leb_skip(data,pos)
        elif op==0x70:
            segment=imm
            if segment>=len(segments): raise ValueError("invalid bind segment")
            offset,pos=uleb(data,pos,len(data))
        elif op==0x80:
            amount,pos=uleb(data,pos,len(data));advance(amount)
        elif op==0x90:
            emit()
        elif op==0xa0:
            amount,pos=uleb(data,pos,len(data));emit(skip=amount)
        elif op==0xb0:
            emit(skip=imm*8)
        elif op==0xc0:
            count,pos=uleb(data,pos,len(data))
            skip,pos=uleb(data,pos,len(data))
            emit(count,skip)
        else:
            raise UnsupportedBind("threaded or unknown bind opcode")
        if ordinal is not None and ordinal>dep_count: raise ValueError("bind ordinal outside dependency list")
    if data and not ended: raise ValueError("missing DONE")
    return rows

def inspect_legacy(data):
    deps,_=read_dependencies(data)
    ncmd,size=struct.unpack_from("<II",data,16)
    pos=32
    segments=[]
    streams={}
    for _ in range(ncmd):
        cmd,length=struct.unpack_from("<II",data,pos)
        if cmd==0x19:
            if length<72: raise ValueError("short segment command")
            segments.append(struct.unpack_from("<Q",data,pos+32)[0])
        elif cmd in (0x22,0x80000022):
            if length!=48: raise ValueError("invalid dyld info command")
            if streams: raise ValueError("duplicate dyld info")
            for key,at in (("bind",16),("weak_bind",24),("lazy",32)):
                streams[key]=struct.unpack_from("<II",data,pos+at)
        pos+=length
    rows=set()
    report={}
    for key,(off,count) in streams.items():
        if not count: continue
        if off<32+size or off+count>len(data):
            report[key]="invalid_extent"
            continue
        if key=="weak_bind":
            # Coalescing records may describe definitions, not imports.
            report[key]="coalescing_not_classified"
            continue
        try:
            observed=decode(data[off:off+count],segments,len(deps),key=="lazy")
        except (ValueError,struct.error) as exc:
            report[key]="uninspected: "+str(exc)
            continue
        rows.update(observed)
        report[key]="decoded"
    return sorted(rows),report
