import unittest
from local_symbol_query import query
ROOT="Payload/A.app/A"
A="Payload/A.app/Frameworks/A"
B="Payload/A.app/Frameworks/B"
NAME="_value"
def fixture(provider="@rpath/A",weak=False):
    report={"images":[{"path":ROOT,"imports":[{"symbol":NAME,"ordinal":1,"declared_provider":provider,"effective_weak":weak}]},{"path":A},{"path":B}]}
    graph={"reachable_candidates":[ROOT,A,B],"edges":[{"consumer":ROOT,"ordinal":1,"declared_path":"@rpath/A","architecture_matching_candidates":[A]},{"consumer":A,"ordinal":1,"declared_path":"@rpath/B","architecture_matching_candidates":[B]}]}
    return report,graph
def rec(symbols=None,libs=None):
    return {"status":"trie_inspected","symbols":symbols or {},"reexport_libraries":libs or []}
def direct():return {"kind":"regular","weak_definition":False}
class Tests(unittest.TestCase):
    def row(self,records,provider="@rpath/A",weak=False):
        r,g=fixture(provider,weak)
        return query(r,g,records,NAME)["rows"][0]
    def test_direct(self):
        r=self.row({A:rec({NAME:direct()})})
        self.assertEqual(r["candidate_paths"][0]["chain"],[{"image":A,"symbol":NAME}])
    def test_renamed(self):
        r=self.row({A:rec({NAME:{"kind":"reexport","provider":"@rpath/B","import_name":"_renamed"}}),B:rec({"_renamed":direct()})})
        self.assertEqual(r["candidate_paths"][0]["chain"][-1],{"image":B,"symbol":"_renamed"})
    def test_whole_reexport(self):
        r=self.row({A:rec(libs=["@rpath/B"]),B:rec({NAME:direct()})})
        self.assertEqual(r["status"],"local_export_candidate_observed")
    def test_missing(self):
        self.assertEqual(self.row({A:rec(libs=["@rpath/B"])})["notes"],["export_trie_not_inspected"])
    def test_system(self):
        r=self.row({},provider="/usr/lib/libSystem.B.dylib")
        self.assertIn("system_provider_not_inspected",r["notes"])
    def test_weak(self):
        self.assertTrue(self.row({},weak=True)["effective_weak"])
    def test_wrong_ordinal(self):
        r,g=fixture()
        r["images"][0]["imports"][0]["ordinal"]=2
        self.assertEqual(query(r,g,{A:rec({NAME:direct()})},NAME)["rows"][0]["status"],"not_observed")
    def test_cycle(self):
        r,g=fixture()
        g["edges"].append({"consumer":B,"ordinal":1,"declared_path":"@rpath/A","architecture_matching_candidates":[A]})
        row=query(r,g,{A:rec(libs=["@rpath/B"]),B:rec(libs=["@rpath/A"])},NAME)["rows"][0]
        self.assertIn("cycle_or_depth",row["notes"])
if __name__=="__main__":unittest.main()
