import struct,unittest
from swift_protocol_inventory import inspect

def fixture(protocol_flags=3,conformance_flags=0,tag=0):
    # Two four-byte records, a 24-byte protocol prefix, a 16-byte conformance prefix.
    start=264
    payload=struct.pack("<ii",8|tag,28)+struct.pack("<6I",protocol_flags,0,0,2,3,0)+struct.pack("<4I",0,0,0,conformance_flags)
    length=start+len(payload)
    cmd=bytearray(232)
    struct.pack_into("<II",cmd,0,0x19,232)
    cmd[8:24]=b"__TEXT"+b"\0"*10
    struct.pack_into("<QQQQIIII",cmd,24,0x100000000,length,0,length,5,5,2,0)
    for i,name in enumerate((b"__swift5_protos",b"__swift5_proto")):
        p=72+80*i
        cmd[p:p+16]=name.ljust(16,b"\0")
        cmd[p+16:p+32]=b"__TEXT"+b"\0"*10
        struct.pack_into("<QQI",cmd,p+32,0x100000000+start+4*i,4,start+4*i)
    return struct.pack("<8I",0xfeedfacf,0x100000c,0,6,1,232,0,0)+cmd+payload

class Tests(unittest.TestCase):
    def test_headers(self):
        r=inspect(fixture(conformance_flags=(1<<8)|(1<<17)))
        self.assertEqual(r["protocols"]["requirement_counts"],{"protocol_requirements":3,"signature_requirements":2})
        self.assertEqual(r["conformances"]["requirement_counts"]["conditional_requirements"],1)
        self.assertEqual(r["conformances"]["flags"]["generic_witness_table"],1)
    def test_protocol_tag(self):
        self.assertEqual(inspect(fixture(tag=1))["protocols"]["record_status"],{"tagged_or_unaligned_unresolved":1})
    def test_protocol_kind(self):
        self.assertEqual(inspect(fixture(protocol_flags=17))["protocols"]["record_status"],{"unsupported_protocol_header":1})
    def test_unknown_flags(self):
        self.assertEqual(inspect(fixture(conformance_flags=1<<18))["conformances"]["record_status"],{"unsupported_conformance_flags":1})
    def test_type_kind(self):
        self.assertEqual(inspect(fixture(conformance_flags=3<<3))["conformances"]["type_reference_kinds"],{"3":1})
    def test_bounds(self):
        with self.assertRaises(ValueError):inspect(fixture()[:-1])
    def test_absence(self):
        self.assertEqual(inspect(struct.pack("<8I",0xfeedfacf,0x100000c,0,6,0,0,0,0))["status"],"sections_not_observed")
if __name__=="__main__":unittest.main()
