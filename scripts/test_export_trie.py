import struct,unittest
from export_trie import decode_trie,inspect_exports,uleb,summarize_exports

def trie(label,terminal):
    edge=label.encode()+b"\0"
    off=2+len(edge)+1
    assert off<128 and len(terminal)<128
    return b"\0\1"+edge+bytes([off,len(terminal)])+terminal+b"\0"

def image(payload,legacy=False,dep=False):
    commands=[]
    if dep:
        path=b"/usr/lib/libExample.dylib\0"
        n=(24+len(path)+7)&~7
        commands.append(struct.pack("<6I",0x8000001f,n,24,0,0,0)+path+bytes(n-24-len(path)))
    length=48 if legacy else 16
    off=32+sum(map(len,commands))+length
    if legacy:
        commands.append(struct.pack("<12I",0x80000022,48,0,0,0,0,0,0,0,0,off,len(payload)))
    else:
        commands.append(struct.pack("<4I",0x80000033,16,off,len(payload)))
    body=b"".join(commands)
    return struct.pack("<8I",0xfeedfacf,0x100000c,0,6,len(commands),len(body),0,0)+body+payload

class Exports(unittest.TestCase):
    def test_direct_and_weak(self):
        for flag,kind in [(0,"regular"),(4,"regular"),(1,"thread_local"),(2,"absolute")]:
            result=decode_trie(trie("_test",bytes([flag,1])),[])
            self.assertEqual(result["_test"]["kind"],kind)
            self.assertEqual(result["_test"]["weak_definition"],bool(flag&4))
    def test_reexport_names(self):
        deps=[{"path":"/usr/lib/libExample.dylib"}]
        for tail,expected in [(b"\0","_test"),(b"_alias\0","_alias")]:
            result=decode_trie(trie("_test",b"\x08\x01"+tail),deps)
            self.assertEqual(result["_test"]["import_name"],expected)
            self.assertEqual(result["_test"]["provider"],deps[0]["path"])
    def test_resolver(self):
        self.assertEqual(decode_trie(trie("_test",b"\x10\x01\x02"),[])["_test"]["kind"],"stub_resolver")
    def test_both_command_formats(self):
        for legacy in (False,True):
            r=inspect_exports(image(trie("_test",b"\x08\x01\0"),legacy,True))
            self.assertEqual(r["status"],"trie_inspected")
            self.assertEqual(r["reexport_libraries"],["/usr/lib/libExample.dylib"])
            self.assertEqual(summarize_exports(r)["entry_counts"],{"reexport":1})
    def test_unknown_not_empty(self):
        r=inspect_exports(struct.pack("<8I",0xfeedfacf,0x100000c,0,6,0,0,0,0))
        self.assertEqual(r["status"],"trie_not_available")
    def test_malformed(self):
        for data in (b"\0\1x\0\0",b"\x7f",trie("_x",b"\x08\x02\0"),trie("_x",b"\x20\x01")):
            with self.assertRaises(ValueError):
                decode_trie(data,[])
        with self.assertRaises(ValueError):
            inspect_exports(image(trie("_x",b"\0\1"))[:-1])
    def test_uleb_bounds(self):
        self.assertEqual(uleb(b"\x81\x01",0,2),(129,2))
        with self.assertRaises(ValueError):
            uleb(b"\xff"*10,0,10)
if __name__=="__main__":
    unittest.main()
