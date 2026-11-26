"""Rebind selected imports in the independently compiled test client only."""
import struct
UIKIT=b"/System/Library/Frameworks/AppIntents.framework/AppIntents"
OVERLAY=b"@rpath/libAppIntentsCompat.dylib"
LOADS={0xc,0x80000018,0x8000001f,0x80000023,0x20}
def rebind(data, symbols, expected):
    def get(fmt, offset): return struct.unpack_from("<"+fmt,data,offset)
    def span(offset,size):
        if offset<0 or size<0 or offset+size>len(data): raise ValueError("out of range")
        return data[offset:offset+size]
    def string(pool,off):
        if not 0<=off<len(pool): raise ValueError("invalid string")
        end=pool.find(b"\0",off)
        if end<0: raise ValueError("unterminated string")
        return pool[off:end]
    if data[:4]!=b"\xcf\xfa\xed\xfe" or get("I",4)[0]!=0x100000c:
        raise ValueError("expected thin arm64")
    nc,sz=get("II",16)
    end=32+sz
    span(32,sz)
    if nc>sz//8: raise ValueError("bad command count")
    pos=32
    libs=[]
    sections=[]
    fix=symtab=dysymtab=None
    for _ in range(nc):
        cmd,ln=get("II",pos)
        if ln<8 or ln%8 or pos+ln>end: raise ValueError("bad load command")
        if cmd in LOADS:
            if ln<24: raise ValueError("short dylib")
            off=get("I",pos+8)[0]
            if off<24: raise ValueError("bad dylib path")
            libs.append(string(span(pos,ln),off))
        elif cmd==0x19:
            if ln<72: raise ValueError("short segment")
            n=get("I",pos+64)[0]
            if 72+80*n>ln: raise ValueError("bad sections")
            for j in range(n):
                at=get("I",pos+72+j*80+48)[0]
                if at: sections.append(at)
        elif cmd==0x80000034:
            if ln<16 or fix is not None: raise ValueError("bad chained command")
            fix=get("II",pos+8)
        elif cmd==2:
            if ln<24: raise ValueError("short symtab")
            symtab=get("IIII",pos+8)
        elif cmd==11:
            if ln<80: raise ValueError("short dysymtab")
            dysymtab=get("II",pos+24)
        elif cmd in (0x22,0x80000022):
            if ln<48 or any(get("I",pos+x)[0] for x in (20,28,36)):
                raise ValueError("legacy binds unsupported")
        elif cmd in (0x21,0x2c):
            if ln<20 or get("I",pos+16)[0]!=0: raise ValueError("encrypted input")
        pos+=ln
    if pos!=end or libs.count(UIKIT)!=1 or not fix:
        raise ValueError("unexpected provider layout")
    old=libs.index(UIKIT)+1
    new=libs.index(OVERLAY)+1 if OVERLAY in libs else len(libs)+1
    if new>240: raise ValueError("unsafe library ordinal")
    fo,fs=fix
    block=span(fo,fs)
    if len(block)<28: raise ValueError("short chained block")
    ver,starts,im,sy,count,fmt,sfmt=struct.unpack_from("<7I",block)
    if ver or fmt!=1 or sfmt or im<28 or im+count*4>sy or sy>len(block):
        raise ValueError("unexpected chained table format")
    names=block[sy:]
    hits=[]
    for i in range(count):
        off=im+i*4
        raw=struct.unpack_from("<I",block,off)[0]
        if raw&255==old:
            name=string(names,raw>>9)
            if name in symbols:
                hits.append((fo+off,raw,name))
    if len(hits)!=expected: raise ValueError(f"expected {expected} imports, found {len(hits)}")
    output=bytearray(data)
    if OVERLAY not in libs:
        name=OVERLAY+b"\0"
        ln=(24+len(name)+7)&~7
        first=min(sections) if sections else 0
        if first<end+ln or any(span(end,ln)): raise ValueError("no verified header padding")
        command=struct.pack("<6I",0xc,ln,24,0,0x10000,0x10000)+name+b"\0"*(ln-24-len(name))
        output[end:end+ln]=command
        struct.pack_into("<II",output,16,nc+1,sz+ln)
    for at,raw,name in hits:
        struct.pack_into("<I",output,at,(raw&~255)|new)
    nlist_count=0
    if symtab:
        so,num,st,ss=symtab
        span(so,num*16)
        pool=span(st,ss)
        first,n=dysymtab if dysymtab else (0,num)
        if first+n>num: raise ValueError("invalid undefined range")
        for i in range(first,first+n):
            at=so+i*16
            si,typ,sec,desc,val=get("IBBHQ",at)
            if typ&0xe0 or typ&0x0e or not typ&1 or desc>>8!=old: continue
            if string(pool,si) in symbols:
                struct.pack_into("<H",output,at+6,(desc&255)|(new<<8))
                nlist_count+=1
    if len(output)!=len(data): raise ValueError("unexpected binary size change")
    # Verify the original table's symbol indices/weak bits and new ordinals.
    for at,raw,name in hits:
        result=struct.unpack_from("<I",output,at)[0]
        if result>>8!=raw>>8 or result&255!=new: raise ValueError("failed import verification")
    return bytes(output),{"chained_count":len(hits),"nlist_count":nlist_count,
         "old_ordinal":old,"new_ordinal":new,"symbols":sorted({h[2].decode() for h in hits})}
