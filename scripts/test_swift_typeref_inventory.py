import struct,unittest
from swift_typeref_inventory import scan,inspect

def image(payload):
    command=bytearray(152)
    struct.pack_into("<II",command,0,0x19,152)
    struct.pack_into("<I",command,64,1)
    command[72:72+16]=b"__swift5_typeref"
    command[88:88+16]=b"__TEXT"+b"\0"*10
    struct.pack_into("<QQI",command,104,0,len(payload),32+152)
    return struct.pack("<8I",0xfeedfacf,0x100000c,0,1,1,152,0,0)+command+payload

class Tests(unittest.TestCase):
    def test_embedded_zero(self):
        r=scan(b"AA\x01\x00\x00\x00\x00V\0Si\0")
        self.assertEqual(r["records"],2)
        self.assertEqual(r["records_with_references"],1)
        self.assertEqual(r["reference_markers"],{"0x01":1})
    def test_absolute_marker_and_padding(self):
        r=scan(b"\0\xff\x18"+b"\0"*8+b"\0")
        self.assertEqual(r["records"],1)
        self.assertEqual(r["reference_markers"],{"0x18":1})
    def test_truncation(self):
        for data in (b"A\x01\x00",b"A\x18"+b"\0"*7,b"Si",b"\x01"+b"\0"*4):
            with self.assertRaises(ValueError): scan(data)
    def test_macho(self):
        r=inspect(image(b"\x02"+b"\0"*4+b"\0"))
        self.assertEqual(r["status"],"framed")
        self.assertEqual(r["reference_markers"],{"0x02":1})
    def test_bounds(self):
        with self.assertRaises(ValueError): inspect(image(b"Si\0")[:-1])
    def test_absence(self):
        r=inspect(struct.pack("<8I",0xfeedfacf,0x100000c,0,1,0,0,0,0))
        self.assertEqual(r["status"],"section_not_observed")
if __name__=="__main__":
    unittest.main()
