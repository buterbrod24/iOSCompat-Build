import io,struct,unittest
from cache_inventory import inspect

def fixture(modern=True):
    data=bytearray(4096)
    data[:16]=b"dyld_v1  arm64e\0"
    mo=512 if modern else 128
    struct.pack_into("<4I",data,16,mo,1,640 if not modern else 0,1 if not modern else 0)
    if modern:
        struct.pack_into("<I",data,216,2)
        struct.pack_into("<I",data,364,0x100200)
        struct.pack_into("<II",data,392,800,1)
        struct.pack_into("<II",data,448,640,1)
    struct.pack_into("<QQQII",data,mo,0x100000,4096,0,5,5)
    struct.pack_into("<QQQII",data,640,0x100900,0,0,1000,0)
    name=b"/usr/lib/libExample.dylib\0"
    data[1000:1000+len(name)]=name
    return data
class Cache(unittest.TestCase):
    def test_modern(self):
        r=inspect(io.BytesIO(fixture()))
        self.assertEqual(r["os_version"],[16,2,0])
        self.assertEqual(r["declared_subcache_count"],1)
        self.assertEqual(r["images"][0]["path"],"/usr/lib/libExample.dylib")
        self.assertTrue(r["images"][0]["local_mapping"])
    def test_legacy(self):
        r=inspect(io.BytesIO(fixture(False)))
        self.assertEqual(r["image_table"],"legacy")
        self.assertIsNone(r["os_version"])
        self.assertEqual(len(r["images"]),1)
    def test_remote_image(self):
        d=fixture()
        struct.pack_into("<Q",d,640,0x200000)
        self.assertFalse(inspect(io.BytesIO(d))["images"][0]["local_mapping"])
    def test_invalid_mapping(self):
        d=fixture()
        struct.pack_into("<Q",d,520,8192)
        with self.assertRaises(ValueError): inspect(io.BytesIO(d))
    def test_bad_path(self):
        d=fixture()
        struct.pack_into("<I",d,664,5000)
        with self.assertRaises(ValueError): inspect(io.BytesIO(d))
    def test_invalid_header(self):
        with self.assertRaises(ValueError): inspect(io.BytesIO(b"bad"))
if __name__=="__main__":
    unittest.main()
