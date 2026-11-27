import unittest
from report_to_inventory import convert, BLOCKS, EXPECTED

def fixture():
    lines = ["iOSCompat Unified Probe 0.6.0","OS: 16.2","Completed 42/42; PASS 38; FAIL 0; EVIDENCE 4; INTERRUPTED 0","OS: Version 16.2 (Build 20C65)"]
    for i,(name,names) in enumerate(EXPECTED.items()):
        lines += [f"START {i+1}: {name}",f"EVIDENCE {name}"]
        lines += [f"{'PRESENT' if j==0 else 'ABSENT'} {symbol}" for j,symbol in enumerate(names)]
    lines += ["START 42: other","ABSENT ignored"]
    return "\n".join(lines)

class ConverterTest(unittest.TestCase):
    def test_scoped(self):
        inv = convert(fixture())
        self.assertEqual(sum(len(x["symbols"]) for x in inv["providers"].values()),21)
        for name,provider in BLOCKS.items():
            record=inv["providers"][provider]
            self.assertEqual(record["symbols"][EXPECTED[name][0]],"present")
            self.assertNotIn("ignored",record["symbols"])
    def test_reject_wrong_build(self):
        with self.assertRaises(ValueError):
            convert(fixture().replace("20C65","wrong"))
    def test_reject_incomplete(self):
        with self.assertRaises(ValueError):
            convert(fixture().replace("Completed 42/42","Completed 41/42"))
        with self.assertRaises(ValueError):
            convert(fixture().replace("ABSENT swift_getTypeByMangledNameInContextInMetadataState2",""))
    def test_reject_same_count_wrong_symbol(self):
        with self.assertRaises(ValueError):
            convert(fixture().replace("ABSENT swift_conformsToProtocol2","ABSENT unrelatedSymbol"))

if __name__ == "__main__":
    unittest.main()
