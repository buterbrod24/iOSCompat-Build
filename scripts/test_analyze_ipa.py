import pathlib, tempfile, unittest, zipfile, struct, json
from analyze_ipa import scan

class AnalyzerTest(unittest.TestCase):
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)/"fixture.ipa"
            # Thin empty Mach-O header: no imports and not complete.
            header = struct.pack("<8I", 0xfeedfacf, 0x100000c, 0, 2, 0, 0, 0, 0)
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("Payload/Test.app/Test", header)
                z.writestr("Payload/Test.app/Frameworks/Bad", b"\xcf\xfa\xed\xfe")
                z.writestr("Payload/Test.app/Fat", b"\xca\xfe\xba\xbe")
                z.writestr("Payload/Test.app/info.txt", "not a binary")
            catalog = {"target":"16.2", "symbols":{}}
            before = p.read_bytes()
            r = scan(p, catalog)
            self.assertEqual(len(r["images"]), 3)
            self.assertFalse(r["images"][0]["complete"])
            self.assertIn("error", r["images"][1])
            self.assertIn("error", r["images"][2])
            self.assertEqual(before, p.read_bytes())

if __name__ == "__main__":
    unittest.main()
