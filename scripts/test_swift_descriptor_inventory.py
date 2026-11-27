import struct,unittest
from swift_descriptor_inventory import inspect

def fixture(tag=0,flags=17|64|128,delta=4,truncate=False):
    # __TEXT includes headers, one type record, then a 20-byte nominal prefix.
    start=184
    length=4
    payload=struct.pack("<i",delta|tag)+struct.pack("<5I",flags,0,0,0,0)
    if truncate: payload=payload[:12]
    size=start+len(payload)
    cmd=bytearray(152)
    struct.pack_into("<II",cmd,0,0x19,152)
    cmd[8:24]=b"__TEXT"+b"\0"*10
    struct.pack_into("<QQQQIIII",cmd,24,0x100000000,size,0,size,5,5,1,0)
    cmd[72:88]=b"__swift5_types\0\0"
    cmd[88:104]=b"__TEXT"+b"\0"*10
    struct.pack_into("<QQI",cmd,104,0x100000000+start,length,start)
    return struct.pack("<8I",0xfeedfacf,0x100000c,0,6,1,152,0,0)+cmd+payload

class Tests(unittest.TestCase):
    def test_header(self):
        r=inspect(fixture())
        self.assertEqual(r["nominal_kinds"],{"struct":1})
        self.assertEqual(r["generic_headers"],1)
        self.assertEqual(r["unique_flag_headers"],1)
    def test_indirect(self):
        self.assertEqual(inspect(fixture(tag=1))["record_status"],{"indirect_unresolved":1})
    def test_unsupported(self):
        self.assertEqual(inspect(fixture(tag=2))["record_status"],{"unsupported_reference_kind":1})
    def test_outside(self):
        self.assertEqual(inspect(fixture(delta=400))["record_status"],{"direct_outside_supported_range":1})
    def test_version(self):
        self.assertEqual(inspect(fixture(flags=17|256))["record_status"],{"unsupported_descriptor_version":1})
    def test_kind(self):
        self.assertEqual(inspect(fixture(flags=3))["record_status"],{"unexpected_descriptor_kind":1})
    def test_truncated_prefix(self):
        self.assertEqual(inspect(fixture(truncate=True))["record_status"],{"truncated_nominal_prefix":1})
    def test_bad_segment(self):
        with self.assertRaises(ValueError): inspect(fixture()[:-1])
if __name__=="__main__": unittest.main()
