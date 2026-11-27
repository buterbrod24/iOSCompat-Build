import unittest,shutil
from swift_symbol_roles import classify,demangle,opaque_pairs

class Roles(unittest.TestCase):
    def test_static(self):
        self.assertEqual(classify(["Static"],["Getter"]),"ordinary_callable")
        self.assertEqual(classify(["Static"],["Variable"]),"unclassified")
    def test_metadata(self):
        self.assertEqual(classify(["TypeMetadataAccessFunction"],[]),"metadata_accessor")
        self.assertEqual(classify(["NominalTypeDescriptor"],[]),"abi_data")
    def test_unknown(self):
        self.assertEqual(classify(["FutureNode"],[]),"unclassified")
        self.assertEqual(classify(["Function","Suffix"],[]),"unclassified")
    def test_pair_requires_label_and_role(self):
        func={"symbol":"$sExampleF","nodes":["Function"],"role":"ordinary_callable","label":"Example() -> some"}
        descriptor={"symbol":"$sExampleFQOMQ","nodes":["OpaqueTypeDescriptor"],"role":"abi_data","label":"opaque type descriptor for <<opaque return type of Example() -> some>>"}
        self.assertEqual(len(opaque_pairs([func,descriptor])["pairs"]),1)
        self.assertEqual(opaque_pairs([descriptor])["unmatched_descriptors"],[descriptor["symbol"]])
        descriptor["label"]="unrelated label"
        self.assertEqual(opaque_pairs([func,descriptor])["pairs"],[])
    @unittest.skipUnless(shutil.which("swift-demangle"),"Swift compiler required")
    def test_real_demangler(self):
        names=["$s7SwiftUI9KeyframesMp","$s7SwiftUI6SpringVMa",
               "$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgF",
               "$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgFQOMQ"]
        got={r["symbol"]:r["role"] for r in demangle(names)}
        self.assertEqual([got[n] for n in names],["abi_data","metadata_accessor","ordinary_callable","abi_data"])
        result=opaque_pairs(demangle(names))
        self.assertEqual(result["pairs"],[{"callable":names[2],"descriptor":names[3]}])
        self.assertEqual(result["unmatched_descriptors"],[])
if __name__=="__main__":
    unittest.main()
