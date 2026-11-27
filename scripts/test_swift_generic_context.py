import struct,unittest
from swift_generic_context import inspect_generic,inspect_pack_shapes

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
    def test_shape_metadata_and_witness(self):
        d=fixture(params=b"\x81",reqs=(0xa0,),keys=3,flags=1)
        d+=struct.pack("<10H",2,1,0,1,0,0,1,2,0,0)
        r=inspect_generic(d,0,len(d))["pack_shapes"]
        self.assertEqual(r["status"],"shape_array_observed")
        self.assertEqual(r["kinds"],{"metadata":1,"witness_table":1})
    def test_pack_shape_truncated(self):
        d=fixture(params=b"\x81",reqs=(),keys=2,flags=1)
        self.assertEqual(inspect_generic(d,0,len(d))["pack_shapes"]["status"],"truncated_pack_header")
    def test_pack_wrong_count(self):
        d=struct.pack("<2H",0,0)
        self.assertEqual(inspect_pack_shapes(d,0,len(d),2,1,0)["status"],"pack_count_mismatch")
    def test_pack_bounds(self):
        for index,shape in ((0,0),(2,0),(1,1)):
            d=struct.pack("<6H",1,1,0,index,shape,0)
            self.assertEqual(inspect_pack_shapes(d,0,len(d),2,1,0)["status"],"pack_index_or_shape_out_of_range")
    def test_pack_order(self):
        d=struct.pack("<10H",2,1,1,2,0,0,0,1,0,0)
        self.assertEqual(inspect_pack_shapes(d,0,len(d),3,1,1)["status"],"unordered_or_duplicate_pack_index")
    def test_missing_pack_flag(self):
        d=fixture(params=b"\x81",reqs=(),keys=2,flags=0)
        self.assertEqual(inspect_generic(d,0,len(d))["pack_shapes"]["status"],"pack_markers_without_header_flag")
if __name__=="__main__":unittest.main()
