import unittest
from audit_impact import impact,PROVIDER,NAMES

class Tests(unittest.TestCase):
    def test_overlap(self):
        rows={(PROVIDER,NAMES[0]):{"required":True,"consumers":{"App","A"}},
              (PROVIDER,NAMES[1]):{"required":False,"consumers":{"App","B"}},
              ("/other",NAMES[2]):{"required":True,"consumers":{"C"}}}
        r=impact(rows)
        self.assertEqual(r["unique_consumers"],3)
        self.assertEqual(r["symbol_consumer_pairs"],4)
        self.assertEqual(r["overlap_histogram"],{1:2,2:1})
        self.assertEqual(r["symbols"][NAMES[1]]["group_strength"],"weak_only")
        self.assertEqual(r["symbols"][NAMES[2]]["status"],"not_observed_in_report")
    def test_empty(self):
        r=impact({})
        self.assertEqual(r["unique_consumers"],0)
        self.assertEqual(r["symbol_consumer_pairs"],0)
        self.assertEqual(r["overlap_histogram"],{})
if __name__=="__main__":
    unittest.main()
