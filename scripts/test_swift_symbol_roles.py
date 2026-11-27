import unittest,shutil
from swift_symbol_roles import classify,demangle

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
    @unittest.skipUnless(shutil.which("swift-demangle"),"Swift compiler required")
    def test_real_demangler(self):
        names=["$s7SwiftUI9KeyframesMp","$s7SwiftUI6SpringVMa",
               "$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgF",
               "$s7SwiftUI10TransitionPAAE9animationyQrAA9AnimationVSgFQOMQ"]
        got={r["symbol"]:r["role"] for r in demangle(names)}
        self.assertEqual([got[n] for n in names],["abi_data","metadata_accessor","ordinary_callable","abi_data"])
if __name__=="__main__":
    unittest.main()
