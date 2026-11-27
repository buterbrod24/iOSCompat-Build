import struct,unittest
from legacy_bind import decode,inspect_legacy,UnsupportedBind

def record(name=b"_x",ordinal=1,weak=False):
    return bytes([0x10|ordinal,0x40|int(weak)])+name+b"\0\x70\x00\x90\x00"

class Legacy(unittest.TestCase):
    def test_regular(self):
        self.assertEqual(decode(record(),[64],1),{("_x",1,False,"legacy_bind")})
    def test_lazy_reset(self):
        self.assertEqual(decode(record()+record(b"_y",2,True),[64],2,True),
                         {("_x",1,False,"legacy_lazy"),("_y",2,True,"legacy_lazy")})
        with self.assertRaises(ValueError): decode(record()+b"\x90\0",[64],1,True)
    def test_special(self):
        self.assertEqual(decode(b"\x3e\x40_x\0\x70\0\x90\0",[64],0),{("_x",-2,False,"legacy_bind")})
    def test_repeated(self):
        self.assertEqual(decode(b"\x11\x41_x\0\x70\0\xc0\x03\x08\0",[64],1),{("_x",1,True,"legacy_bind")})
    def test_bad(self):
        for d in (record()[:-1],b"\x11\x40_x\0\x70\x40\x90\0",b"\x12\x40_x\0\x70\0\x90\0",b"\x20\x80"):
            with self.assertRaises(ValueError): decode(d,[64],1)
        with self.assertRaises(UnsupportedBind): decode(b"\xd0\0",[64],1)
    def test_macho_integration(self):
        path=b"/usr/lib/test.dylib\0"
        n=(24+len(path)+7)&~7
        dep=struct.pack("<6I",0xc,n,24,0,0,0)+path+bytes(n-24-len(path))
        seg=struct.pack("<II16s4Q4I",0x19,72,b"__DATA",0,4096,0,4096,3,3,0,0)
        data=record()
        off=32+len(dep)+len(seg)+48
        dyld=struct.pack("<12I",0x80000022,48,0,0,off,len(data),off+len(data),1,0,0,0,0)
        cmds=dep+seg+dyld
        image=struct.pack("<8I",0xfeedfacf,0x100000c,0,6,3,len(cmds),0,0)+cmds+data+b"\0"
        rows,report=inspect_legacy(image)
        self.assertEqual(rows,[("_x",1,False,"legacy_bind")])
        self.assertEqual(report,{"bind":"decoded","weak_bind":"coalescing_not_classified"})
if __name__=="__main__":
    unittest.main()
