import unittest
from audit_coverage import read_audit,compare

REPORT="""Example selected-export audit
Distinct symbols: 4; per-binary records: 5; strong distinct: 3.

SYMBOL DETAILS
/A | strong | _$sTest
  App
  Framework
/A | weak only | _other
  App
/B | strong | _swift_test
  App
/B | strong | _$sTest
  Framework
"""
CAT={"schema":1,"target":"16.2","symbols":{
    "$sTest":{"provider":"/A","status":"candidate_device_tested"},
    "swift_test":{"provider":"/B","status":"missing_unresolved"}}}

class Tests(unittest.TestCase):
    def test_exact_provider_and_normalization(self):
        r=compare(read_audit(REPORT),CAT)
        self.assertEqual(r["symbols"],4)
        self.assertEqual(r["strong"],3)
        self.assertEqual(r["consumer_records"],5)
        self.assertEqual(r["evidence"]["candidate_device_tested"]["strong"],1)
        self.assertEqual(r["evidence"]["provider_mismatch"]["strong"],1)
        self.assertEqual(r["evidence"]["missing_unresolved"]["strong"],1)
        self.assertEqual(r["evidence"]["not_cataloged"]["weak_only"],1)
    def test_truncation_detected(self):
        with self.assertRaises(ValueError):
            read_audit(REPORT.rsplit("  Framework",1)[0])
    def test_duplicate_consumer(self):
        with self.assertRaises(ValueError):
            read_audit(REPORT.replace("  App\n  Framework","  App\n  App",1))
    def test_duplicate_symbol(self):
        with self.assertRaises(ValueError):
            read_audit(REPORT.replace("/A | weak only | _other","/A | weak only | _$sTest"))
    def test_orphan(self):
        with self.assertRaises(ValueError):
            read_audit(REPORT.replace("SYMBOL DETAILS\n","SYMBOL DETAILS\n  App\n"))
    def test_catalog_unknown(self):
        with self.assertRaises(ValueError):
            compare(read_audit(REPORT),{"schema":1,"target":"17.0","symbols":{}})
        with self.assertRaises(ValueError):
            compare(read_audit(REPORT),{"schema":1,"target":"16.2","symbols":{"other":{"provider":"/A","status":"works"}}})
if __name__=="__main__":
    unittest.main()
