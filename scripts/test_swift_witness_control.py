import struct,unittest
from swift_witness_control import inspect_witness_control

class Tests(unittest.TestCase):
    def test_generic_control(self):
        d=bytes(16)+struct.pack("<HHII",3,5,0,1)
        r=inspect_witness_control(d,0,len(d),131072)
        self.assertEqual(r["status"],"trailing_headers_observed")
        self.assertEqual(r["generic_witness_control"],{"template_words":3,"private_words":2,
            "requires_instantiation_bit":True,"instantiator_field_nonzero":False,"private_data_field_nonzero":True})
    def test_skip_arrays(self):
        d=bytes(16+4+12+8)+struct.pack("<HHII",4,1,1,0)
        r=inspect_witness_control(d,0,len(d),64|256|(1<<24)|131072)
        self.assertEqual(r["generic_witness_control"]["template_words"],4)
    def test_resilient(self):
        d=bytes(16)+struct.pack("<I",2)+bytes(16)+struct.pack("<HHII",3,0,0,0)
        r=inspect_witness_control(d,0,len(d),65536|131072)
        self.assertEqual(r["resilient_witness_records"],2)
        self.assertEqual(r["generic_witness_control"]["private_words"],0)
    def test_truncated(self):
        for size,flags,status in [(15,0,"truncated_conformance_prefix"),
            (16,256,"truncated_preceding_arrays"),(19,65536,"truncated_resilient_header"),
            (20,131072,"truncated_generic_witness_control")]:
            self.assertEqual(inspect_witness_control(bytes(size),0,size,flags)["status"],status)
    def test_oversize(self):
        d=bytes(16)+struct.pack("<I",0xffffffff)
        self.assertEqual(inspect_witness_control(d,0,len(d),65536)["status"],"truncated_or_oversized_resilient_array")
    def test_neighbor_bound(self):
        d=bytes(100)
        self.assertEqual(inspect_witness_control(d,0,24,131072)["status"],"truncated_generic_witness_control")
if __name__=="__main__":unittest.main()
