import unittest
from reexport_graph import trace

def record(symbols=None,libs=(),status="trie_inspected",arch=(1,0)):
    return {"symbols":symbols or {},"reexport_libraries":list(libs),"status":status,"architecture":arch}
def direct():
    return {"kind":"regular","weak_definition":False}
def redirect(lib,name):
    return {"kind":"reexport","provider":lib,"import_name":name}

class Graph(unittest.TestCase):
    def test_direct(self):
        r=trace({"A":record({"_x":direct()})},"A","_x")
        self.assertEqual(r["status"],"candidate_path_found")
        self.assertEqual(len(r["paths"][0]["chain"]),1)
    def test_chain_and_rename(self):
        r=trace({"A":record(libs=["B"]),"B":record({"_x":redirect("C","_y")}),"C":record({"_y":direct()})},"A","_x")
        self.assertEqual(r["paths"][0]["chain"][-1],{"provider":"C","symbol":"_y"})
    def test_cycle(self):
        r=trace({"A":record(libs=["B"]),"B":record(libs=["A"])},"A","_x")
        self.assertEqual(r["status"],"not_observed")
        self.assertTrue(any("cycle" in b for b in r["blockers"]))
    def test_missing_and_uninspected(self):
        r=trace({"A":record(libs=["B","C"]),"C":record(status="trie_not_available")},"A","_x")
        self.assertEqual(len(r["blockers"]),2)
    def test_architecture(self):
        r=trace({"A":record(libs=["B"]),"B":record({"_x":direct()},arch=(2,0))},"A","_x")
        self.assertEqual(r["status"],"not_observed")
        self.assertTrue(r["blockers"])
    def test_ordinary_dependency_not_followed(self):
        a=record()
        a["dependencies"]=["B"]
        self.assertEqual(trace({"A":a,"B":record({"_x":direct()})},"A","_x")["status"],"not_observed")
if __name__=="__main__":
    unittest.main()
