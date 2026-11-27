import struct, unittest
from backdeploy_markers import inspect_markers, annotate_imports

def fixture(rows):
    pool=b"\0"
    symbols=b""
    for name,typ,sect in rows:
        index=len(pool)
        pool+=name.encode()+b"\0"
        symbols+=struct.pack("<IBBHQ",index,typ,sect,0,0x1000)
    return (struct.pack("<8I",0xfeedfacf,0x100000c,0,2,1,24,0,0)
            +struct.pack("<6I",2,24,56,len(rows),56+len(symbols),len(pool))
            +symbols+pool)

class Markers(unittest.TestCase):
    def test_exact_local_pair(self):
        image={"backdeploy":inspect_markers(fixture([
            ("_$sTestFTwb",0xe,1),("_$sTestFTwB",0xf,1),
            ("_$sImportedFTwB",1,0),("_$sDebugFTwb",0xee,1),
            ("_notSwiftTwB",0xe,1),("_$sOtherFTwB",0xe,1)])),
            "imports":[{"symbol":"_$sTestF","weak":True},{"symbol":"_$sOtherF"},
                       {"symbol":"_$sImportedF"}]}
        annotate_imports(image)
        self.assertEqual([x["backdeploy_name_evidence"] for x in image["imports"]],
                         ["thunk_and_fallback_names","partial_name_match","not_observed"])
        self.assertTrue(image["imports"][0]["weak"])
        self.assertEqual(len(image["backdeploy"]["markers"]),2)
    def test_no_table(self):
        data=struct.pack("<8I",0xfeedfacf,0x100000c,0,2,0,0,0,0)
        self.assertEqual(inspect_markers(data)["symbol_table"],"unavailable")
    def test_malformed(self):
        with self.assertRaises(ValueError):
            inspect_markers(fixture([("_$sTestFTwB",0xe,1)])[:-1])

if __name__=="__main__":
    unittest.main()
