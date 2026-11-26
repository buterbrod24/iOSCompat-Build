import unittest
from report_to_inventory import convert, BLOCKS

def fixture():
    lines = ["iOSCompat Unified Probe 0.6.0","OS: 16.2","Completed 42/42; PASS 38; FAIL 0; EVIDENCE 4; INTERRUPTED 0","OS: Version 16.2 (Build 20C65)"]
    for i,(name,count) in enumerate(zip(BLOCKS,(10,5,6))):
        lines += [f"START {i+1}: {name}",f"EVIDENCE {name}"]
        lines += [f"{'PRESENT' if j==0 else 'ABSENT'} fixture{j}" for j in range(count)]
    lines += ["START 42: other","ABSENT ignored"]
    return "\n".join(lines)

class ConverterTest(unittest.TestCase):
    def test_scoped(self):
        inv = convert(fixture())
        self.assertEqual(sum(len(x["symbols"]) for x in inv["providers"].values()),21)
        for record in inv["providers"].values():
            self.assertEqual(record["symbols"]["fixture0"],"present")
            self.assertNotIn("ignored",record["symbols"])
    def test_reject_wrong_build(self):
        with self.assertRaises(ValueError):
            convert(fixture().replace("20C65","wrong"))
    def test_reject_incomplete(self):
        with self.assertRaises(ValueError):
            convert(fixture().replace("Completed 42/42","Completed 41/42"))
        with self.assertRaises(ValueError):
            convert(fixture().replace("ABSENT fixture9",""))

if __name__ == "__main__":
    unittest.main()
