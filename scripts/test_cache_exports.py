import io,struct,unittest
from cache_exports import VMReader,inspect_image

def fixture(legacy=False,bad=False):
    address=0x100000
    vm=0x300000
    linkoff=0x8000
    trie=b"\x00\x01_x\x00\x06\x02\x00\x01\x00"
    def segment(name,addr,size,off):
        return struct.pack("<II16s4Q4I",0x19,72,name,addr,size,off,size,5,5,0,0)
    name=b"/usr/lib/test.dylib\0"
    n=(24+len(name)+7)&~7
    ident=struct.pack("<6I",0xd,n,24,0,0,0)+name+bytes(n-24-len(name))
    offset=linkoff+16 if not bad else linkoff-1
    export=(struct.pack("<12I",0x80000022,48,0,0,0,0,0,0,0,0,offset,len(trie)) if legacy
            else struct.pack("<4I",0x80000033,16,offset,len(trie)))
    cmds=segment(b"__TEXT",address,4096,0)+segment(b"__LINKEDIT",vm,4096,linkoff)+ident+export
    a=struct.pack("<8I",0xfeedfacf,0x100000c,2,6,4,len(cmds),0,0)+cmds
    a+=bytes(4096-len(a))
    b=bytes(16)+trie+bytes(4096-16-len(trie))
    mappings=[dict(address=address,size=4096,file_offset=0,cache_uuid="A"),
              dict(address=vm,size=4096,file_offset=0,cache_uuid="B")]
    files={"A":(io.BytesIO(a),len(a)),"B":(io.BytesIO(b),len(b))}
    return VMReader(mappings,files),address

class CacheExports(unittest.TestCase):
    def test_split_linkedit(self):
        for legacy in (False,True):
            r,a=fixture(legacy)
            result=inspect_image(r,a)
            self.assertEqual(result["symbols"]["_x"]["kind"],"regular")
            self.assertEqual(result["install_name"],"/usr/lib/test.dylib")
    def test_missing_mapping(self):
        r,a=fixture()
        r.ranges.pop()
        r.starts.pop()
        with self.assertRaises(ValueError): inspect_image(r,a)
    def test_outside_linkedit(self):
        r,a=fixture(bad=True)
        with self.assertRaises(ValueError): inspect_image(r,a)
    def test_cross_boundary(self):
        r,a=fixture()
        with self.assertRaises(ValueError): r.read(a+4095,2)
    def test_wrong_header(self):
        r,a=fixture()
        with self.assertRaises(ValueError): inspect_image(r,a+1)
if __name__=="__main__":
    unittest.main()
