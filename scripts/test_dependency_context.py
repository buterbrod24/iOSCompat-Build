import unittest
from dependency_context import trace
ROOT="Payload/A.app/A"
A="Payload/A.app/Frameworks/A.dylib"
B="Payload/A.app/Frameworks/B.dylib"
OTHER="Payload/A.app/PlugIns/E.appex/E"
def image(path,deps=(),rpaths=(),**extra):
    return dict(path=path,cpu_type=0x100000c,cpu_subtype=0,
                dependencies=[{"path":v,"kind":"load","ordinal":i+1} for i,v in enumerate(deps)],
                rpaths=list(rpaths),**extra)
class Tests(unittest.TestCase):
    def test_inheritance(self):
        r=trace({"images":[image(ROOT,["@rpath/A.dylib"],["@executable_path/Frameworks"]),
            image(A,["@rpath/B.dylib"]),image(B),image(OTHER)]},ROOT)
        self.assertEqual(set(r["reachable_candidates"]),{ROOT,A,B})
        self.assertEqual(r["other_images"],[OTHER])
        self.assertEqual(r["edges"][1]["architecture_matching_candidates"],[B])
    def test_executable_and_loader(self):
        r=trace({"images":[image(ROOT,["@loader_path/Frameworks/A.dylib"]),
            image(A,["@executable_path/Frameworks/B.dylib"]),image(B)]},ROOT)
        self.assertEqual(len(r["reachable_candidates"]),3)
    def test_cycle(self):
        r=trace({"images":[image(ROOT,["@loader_path/Frameworks/A.dylib"]),
            image(A,["@executable_path/A"])]},ROOT)
        self.assertEqual(r["contexts"],2)
        self.assertFalse(r["limits"])
    def test_system_and_missing(self):
        r=trace({"images":[image(ROOT,["/usr/lib/libSystem.B.dylib","@rpath/X"])]},ROOT)
        self.assertEqual(r["edge_counts"],{"no_local_candidate_observed":1,"system_unverified":1})
    def test_ambiguous(self):
        alt="Payload/A.app/Alt/A.dylib"
        r=trace({"images":[image(ROOT,["@rpath/A.dylib"],["@loader_path/Frameworks","@loader_path/Alt"]),image(A),image(alt)]},ROOT)
        self.assertEqual(r["edges"][0]["architecture_matching_candidates"],sorted([A,alt]))
    def test_uninspected(self):
        r=trace({"images":[image(ROOT,["@loader_path/Frameworks/A.dylib"]),image(A,error="fat")]},ROOT)
        self.assertEqual(r["edges"][0]["uninspected_or_other_arch"],[A])
        self.assertEqual(r["reachable_candidates"],[ROOT])
    def test_bad_path(self):
        for bad in (ROOT,"Payload/A.app/../B"):
            with self.assertRaises(ValueError):trace({"images":[image(ROOT),image(bad)]},ROOT)
    def test_unknown_runpath(self):
        r=trace({"images":[image(ROOT,["@rpath/A.dylib"],["/private/unknown"])]},ROOT)
        self.assertEqual(r["notes"],{"unsupported_rpath_declarations":1})
if __name__=="__main__":unittest.main()
