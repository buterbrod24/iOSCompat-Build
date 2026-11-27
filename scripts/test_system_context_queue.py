import unittest
from system_context_queue import classify
ROOT="Payload/A.app/A"
LIB="Payload/A.app/Frameworks/B"
OTHER="Payload/A.app/PlugIns/E.appex/E"
CORE="/usr/lib/swift/libswiftCore.dylib"
OBS="/usr/lib/swift/libswiftObservation.dylib"
def row(symbol="_swift_conformsToProtocol2",provider=CORE,native="absent",status="missing_unresolved",weak=False):
    return {"symbol":symbol,"declared_provider":provider,"native_export":native,
            "status":status,"catalog_provider_match":True,"weak":weak}
def image(path,rows):
    return {"path":path,"cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":rows,
            "dependencies":[{"ordinal":1,"kind":"load","path":"@loader_path/Frameworks/B"}] if path==ROOT else []}
def report(a,b=(),c=()):
    return {"schema":10,"target":"16.2","inventory_build":"20C65",
            "images":[image(ROOT,a),image(LIB,b),image(OTHER,c)]}
class Tests(unittest.TestCase):
    def test_scopes_and_dedup(self):
        r=classify(report([row()],[row()],[row("_other")]),ROOT)
        self.assertEqual(r["root_candidate_union"]["unique_import_groups"],1)
        self.assertEqual(r["root_candidate_union"]["items"][0]["images"],sorted([ROOT,LIB]))
        self.assertEqual(r["scopes"]["other_images"]["unique_import_groups"],1)
    def test_independent_candidate(self):
        r=classify(report([row("_observation",OBS,"absent","candidate_independent_device_tested")]),ROOT)
        self.assertEqual(r["root_candidate_union"]["counts"],{"review_independent_device_tested_candidate":1})
    def test_weak_and_strong(self):
        r=classify(report([row(weak=True)],[row()]),ROOT)
        self.assertEqual(r["scopes"]["root"]["counts"],{"investigate_weak_absence":1})
        self.assertEqual(r["root_candidate_union"]["counts"],{"investigate_required_absence":1})
    def test_conflict(self):
        r=classify(report([row(native="present")]),ROOT)
        self.assertEqual(r["root_candidate_union"]["counts"],{"conflicting_evidence":1})
    def test_exclude_local(self):
        r=classify(report([row(provider="@rpath/B"),row(provider=None)]),ROOT)
        self.assertEqual(r["root_candidate_union"]["unique_import_groups"],0)
    def test_unknown(self):
        r=classify(report([row(native="unknown",status="unknown")]),ROOT)
        self.assertEqual(r["root_candidate_union"]["counts"],{"unknown":1})
    def test_wrong_schema(self):
        r=report([])
        r["schema"]=9
        with self.assertRaises(ValueError):classify(r,ROOT)
if __name__=="__main__":unittest.main()
