"""Read-only import table inspection for thin little-endian Mach-O 64."""
import struct
import zlib

def read_imports(data):
    def unpack(fmt, off):
        return struct.unpack_from("<"+fmt, data, off)
    def span(off, size):
        if off < 0 or size < 0 or off + size > len(data):
            raise ValueError("table outside Mach-O")
        return data[off:off+size]
    def string(pool, off):
        if not 0 <= off < len(pool):
            raise ValueError("invalid string offset")
        end = pool.find(b"\0", off)
        if end < 0:
            raise ValueError("unterminated symbol")
        return pool[off:end].decode("utf-8", "replace")
    if len(data) < 32 or unpack("I",0)[0] != 0xfeedfacf:
        raise ValueError("expected thin little-endian Mach-O 64")
    ncmd, size = unpack("II",16)
    span(32,size)
    if ncmd > size // 8:
        raise ValueError("bad command count")
    symtab = dysymtab = chained = None
    legacy = False
    pos = 32
    for _ in range(ncmd):
        cmd, length = unpack("II",pos)
        if length < 8 or length % 8 or pos + length > 32 + size:
            raise ValueError("bad load command size")
        if cmd == 2:
            if length < 24: raise ValueError("short symtab")
            symtab = unpack("IIII",pos+8)
        elif cmd == 11:
            if length < 80: raise ValueError("short dysymtab")
            dysymtab = unpack("II",pos+24)
        elif cmd == 0x80000034:
            if length < 16: raise ValueError("short chained fixups command")
            chained = unpack("II",pos+8)
        elif cmd in (0x22,0x80000022):
            if length < 48: raise ValueError("short dyld info")
            legacy |= any(unpack("I",pos+x)[0] for x in (20,28,36))
        pos += length
    if pos != 32+size: raise ValueError("inconsistent load commands")
    rows = set()
    sources = []
    if symtab:
        so, count, st, length = symtab
        span(so,count*16)
        strings = span(st,length)
        first, number = dysymtab if dysymtab else (0,count)
        if first+number > count: raise ValueError("bad undefined symbol range")
        for idx in range(first,first+number):
            name, typ, sect, desc, value = unpack("IBBHQ",so+idx*16)
            if typ & 0xe0 or typ & 0x0e != 0 or not typ & 1 or not name:
                continue
            rows.add((string(strings,name), (desc>>8)&255, bool(desc&0x40), "nlist"))
        sources.append("nlist")
    if chained:
        off, size = chained
        block = span(off,size)
        if len(block)<28: raise ValueError("short chained fixups")
        ver, starts, imports, symbols, count, fmt, sfmt = struct.unpack_from("<7I",block)
        if ver != 0 or fmt not in (1,2,3) or sfmt not in (0,1):
            raise ValueError("unsupported chained import format")
        width = {1:4,2:8,3:16}[fmt]
        if imports > len(block) or count > (len(block)-imports)//width or symbols > len(block):
            raise ValueError("bad chained offsets")
        pool = block[symbols:]
        if sfmt == 1:
            obj = zlib.decompressobj()
            pool = obj.decompress(pool, 64*1024*1024)
            if not obj.eof: raise ValueError("compressed symbol pool incomplete or too large")
        for idx in range(count):
            at = imports+idx*width
            if fmt == 3:
                raw = struct.unpack_from("<Q",block,at)[0]
                ordinal, weak, name = raw&65535, bool(raw&65536), raw>>32
            else:
                raw = struct.unpack_from("<I",block,at)[0]
                ordinal, weak, name = raw&255, bool(raw&256), raw>>9
            rows.add((string(pool,name),ordinal,weak,"chained"))
        sources.append("chained")
    # Classical dyld bind streams are deliberately not claimed as decoded.
    complete = bool(chained) and not legacy
    return sorted(rows), sources, complete

def read_dependencies(data):
    """Return declared load commands in library-ordinal order, not resolved paths."""
    if len(data) < 32 or struct.unpack_from("<I", data)[0] != 0xfeedfacf:
        raise ValueError("expected thin little-endian Mach-O 64")
    ncmd, size = struct.unpack_from("<II", data, 16)
    if size > len(data)-32 or ncmd > size//8:
        raise ValueError("invalid load commands")
    kinds = {0xc:"load", 0x80000018:"weak", 0x8000001f:"reexport",
             0x20:"lazy", 0x80000023:"upward"}
    deps, rpaths = [], []
    pos = 32
    for _ in range(ncmd):
        if pos+8 > 32+size:
            raise ValueError("truncated load command")
        cmd, length = struct.unpack_from("<II", data, pos)
        if length < 8 or length % 8 or pos+length > 32+size:
            raise ValueError("invalid load command size")
        if cmd in kinds or cmd == 0x8000001c:
            minimum = 24 if cmd in kinds else 12
            if length < minimum:
                raise ValueError("short path command")
            offset = struct.unpack_from("<I", data, pos+8)[0]
            if not minimum <= offset < length:
                raise ValueError("invalid path offset")
            end = data.find(b"\0", pos+offset, pos+length)
            if end < 0:
                raise ValueError("unterminated dependency path")
            name = data[pos+offset:end].decode("utf-8", "replace")
            if cmd in kinds:
                deps.append({"ordinal":len(deps)+1, "kind":kinds[cmd], "path":name})
            else:
                rpaths.append(name)
        pos += length
    if pos != 32+size:
        raise ValueError("inconsistent load commands")
    return deps, rpaths

def declared_provider(deps, ordinal, source):
    # Only ordinary ordinals are mapped; special or ambiguous values stay unknown.
    # Chained ordinals are unsigned in read_imports and may encode negative values.
    if source == "nlist" and ordinal >= 0xfe:
        return None
    if source == "chained" and (0xf1 <= ordinal <= 0xff or ordinal >= 0xfff1):
        return None
    if 1 <= ordinal <= len(deps):
        return deps[ordinal-1]["path"]
    return None
