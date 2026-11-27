import struct,unittest
from swift_generic_context import inspect_generic

def fixture(params=b"\x80",reqs=(128,),keys=2,flags=0):
    data=bytearray(36)+struct.pack("<4H",len(params),len(reqs),keys,flags)+params
    data+=b"\0"*((-len(data))%4)
    for req in reqs:
        data+=struct.pack("<3I",req,0,0)
    return bytes(data)
class Tests(unittest.TestCase):
    def test_normal(self):
        d=fixture()
        r=inspect_generic(d,0,len(d))
        self.assertEqual(r["status"],"fixed_arrays_observed")
        self.assertEqual(r["parameter_kinds"],{"type":1})
        self.assertEqual(r["requirement_kinds"],{"protocol":1})
        self.assertEqual(r["key_arguments"],2)
    def test_pack(self):
        d=fixture(params=b"\x81",reqs=(0xa0,),keys=3,flags=1)
        r=inspect_generic(d,0,len(d))
        self.assertTrue(r["nonzero_legacy_extra_field"])
        self.assertEqual(r["parameter_kinds"],{"type_pack":1})
        self.assertEqual(r["pack_requirements"],1)
    def test_unknown_flags(self):
        d=fixture(flags=2)
        self.assertEqual(inspect_generic(d,0,len(d))["status"],"unknown_generic_flags")
    def test_reserved_param(self):
        d=fixture(params=b"\xc0")
        self.assertEqual(inspect_generic(d,0,len(d))["status"],"unknown_parameter_descriptor")
    def test_reserved_req(self):
        d=fixture(reqs=(64,))
        self.assertEqual(inspect_generic(d,0,len(d))["status"],"unknown_requirement_descriptor")
    def test_bounds(self):
        d=fixture()
        self.assertEqual(inspect_generic(d,0,43)["status"],"truncated_generic_header")
        self.assertEqual(inspect_generic(d,0,len(d)-1)["status"],"truncated_generic_arrays")
    def test_alignment(self):
        d=fixture(params=b"\x80\x80\x80",reqs=(1,31))
        r=inspect_generic(d,0,len(d))
        self.assertEqual(r["requirement_kinds"],{"layout":1,"same_type":1})
if __name__=="__main__":unittest.main()
