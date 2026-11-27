import unittest
from system_export_report import convert
P="/usr/lib/swift/libswiftCore.dylib"
EXPECTED={P:["swift_test"]}
def report(first="ABSENT",tree="PRESENT",handles="OPEN\tOPEN"):
    return "\n".join(["iOSCompat System Export Probe 0.1.0","OS: Version 16.2 (Build 20C65)","START","PROVIDER\t"+P,"HANDLES\t"+handles,"LOOKUP\tswift_test\t"+first+"\t"+tree,"TOTAL\t1","COMPLETE"])
class Tests(unittest.TestCase):
    def test_scoped(self):
        r=convert(report(),EXPECTED)
        self.assertEqual(r["providers"][P]["symbols"],{"swift_test":"absent"})
        self.assertEqual(r["providers"][P]["lookup_pairs"]["swift_test"]["tree"],"present")
    def test_unavailable(self):
        r=convert(report("UNKNOWN","UNKNOWN","UNAVAILABLE\tUNAVAILABLE"),EXPECTED)
        self.assertEqual(r["providers"][P]["symbols"],{})
    def test_conflict(self):
        self.assertEqual(convert(report("PRESENT","ABSENT"),EXPECTED)["providers"][P]["symbols"],{})
    def test_complete(self):
        with self.assertRaises(ValueError):convert(report().replace("COMPLETE",""),EXPECTED)
    def test_exact_name(self):
        with self.assertRaises(ValueError):convert(report().replace("swift_test","swift_other"),EXPECTED)
    def test_failed_handle(self):
        with self.assertRaises(ValueError):convert(report(handles="UNAVAILABLE\tOPEN"),EXPECTED)
if __name__=="__main__":unittest.main()
