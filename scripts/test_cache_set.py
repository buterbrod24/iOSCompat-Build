import io,struct,unittest,uuid
from cache_set import declarations,verify

def fixture(modern):
    d=bytearray(4096)
    d[:16]=b"dyld_v1  arm64e\0"
    struct.pack_into("<I",d,16,512 if modern else 448)
    struct.pack_into("<Q",d,224,0x100000)
    struct.pack_into("<II",d,392,800,1)
    d[800:816]=uuid.UUID(int=2).bytes
    struct.pack_into("<Q",d,816,0x2000)
    if modern: d[824:831]=b".1.data"
    return d

def record(n,address,arch="arm64e"):
    return {"uuid":str(uuid.UUID(int=n)),"architecture":arch,
            "platform":2,"os_version":[16,2,0],
            "mappings":[{"address":address,"size":4096,"file_offset":0}],"images":[]}

class CacheSet(unittest.TestCase):
    def test_formats(self):
        for modern in (False,True):
            rows=declarations(io.BytesIO(fixture(modern)))
            self.assertEqual(rows[0]["expected_start"],0x102000)
            self.assertEqual(rows[0]["suffix"],".1.data" if modern else ".1")
    def test_match(self):
        root=record(1,0x100000)
        root["images"]=[{"path":"/usr/lib/test","address":0x102100}]
        r=verify(root,declarations(io.BytesIO(fixture(True))),[record(2,0x102000)])
        self.assertEqual(r["status"],"declared_parts_matched")
        self.assertEqual(r["images"][0]["cache_owners"],[str(uuid.UUID(int=2))])
    def test_missing_and_wrong_uuid(self):
        r=verify(record(1,0x100000),declarations(io.BytesIO(fixture(True))),[record(3,0x102000)])
        self.assertEqual(len(r["missing"]),1)
        self.assertTrue(r["issues"])
    def test_arch_and_address(self):
        expected=declarations(io.BytesIO(fixture(True)))
        for part in (record(2,0x102000,"arm64"),record(2,0x103000)):
            self.assertEqual(verify(record(1,0x100000),expected,[part])["accepted_parts"],0)
    def test_overlap(self):
        root=record(1,0x100000)
        root["mappings"][0]["size"]=0x4000
        self.assertIn("overlapping mappings across cache parts",
                      verify(root,declarations(io.BytesIO(fixture(True))),[record(2,0x102000)])["issues"])
    def test_bad_suffix(self):
        d=fixture(True)
        d[824:829]=b"./bad"
        with self.assertRaises(ValueError): declarations(io.BytesIO(d))
    def test_no_declarations(self):
        self.assertEqual(verify(record(1,0x100000),None,[])["status"],"incomplete_or_unverified")
if __name__=="__main__":
    unittest.main()
