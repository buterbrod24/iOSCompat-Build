import unittest
from value_witness_flags import decode
class Tests(unittest.TestCase):
    def test_alignment(self):
        for size in (1,2,4,8,16,32,64,128,256):
            r=decode(size-1,"5.7")
            self.assertEqual(r["alignment"],size)
            self.assertTrue(r["alignment_power_of_two"])
    def test_invalid_alignment(self):
        self.assertFalse(decode(5,"5.9")["alignment_power_of_two"])
    def test_version(self):
        self.assertEqual(decode(0x800000,"5.7")["unknown_bits"],0x800000)
        self.assertTrue(decode(0x800000,"5.9")["flags"]["noncopyable"])
    def test_common_flags(self):
        for version in ("5.7","5.9"):
            r=decode(0x7b0007,version)
            self.assertTrue(all(v for k,v in r["flags"].items() if k!="noncopyable"))
            self.assertEqual(r["unknown_bits"],0)
    def test_reserved(self):
        self.assertEqual(decode(0x80000400,"5.9")["unknown_bits"],0x80000400)
    def test_invalid(self):
        for v in (-1,2**32,True,"7"):
            with self.assertRaises(ValueError): decode(v,"5.7")
        with self.assertRaises(ValueError): decode(0,"6.0")
if __name__=="__main__":unittest.main()
