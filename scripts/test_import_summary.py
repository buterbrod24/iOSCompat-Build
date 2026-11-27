import unittest
from import_summary import summarize

class SummaryTest(unittest.TestCase):
    def test_grouping_and_priority(self):
        def row(symbol, weak=False, native="unknown", status="unknown", provider="/usr/lib/test"):
            return dict(symbol=symbol,weak=weak,native_export=native,status=status,
                        declared_provider=provider,catalog_provider_match=status!="unknown")
        a={"path":"A","cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":[
            row("_missing",True,"absent"),row("_candidate",False,"absent","candidate_device_tested"),
            row("_weak",True,"absent"),row("_unknown"),row("_native",False,"present")]}
        b={"path":"B","cpu_type":0x100000c,"cpu_subtype":0,"complete":False,"imports":[
            row("_missing",False,"absent"),row("_missing",False,"absent",provider="/usr/lib/other")]}
        r=summarize([a,b])
        self.assertEqual(r["unique_import_groups"],6)
        self.assertEqual(r["counts"]["investigate_required_absence"],2)
        self.assertEqual(r["counts"]["review_tested_candidate"],1)
        self.assertEqual(r["counts"]["investigate_weak_absence"],1)
        self.assertEqual(r["counts"]["native_lookup_present"],1)
        self.assertEqual(r["counts"]["unknown"],1)
        self.assertEqual(r["incomplete_images"],["B"])
        shared=next(x for x in r["items"] if x["images"]==["A","B"])
        self.assertTrue(shared["required"])
    def test_observation_candidate_not_certified(self):
        row={"symbol":"_$s11Observation10ObservableMp","declared_provider":"/usr/lib/swift/libswiftObservation.dylib",
             "native_export":"unknown","status":"candidate_internal_device_tested_stock_linked",
             "catalog_provider_match":True,"weak":False}
        image={"path":"A","cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":[row]}
        self.assertEqual(summarize([image])["counts"],{"verify_independent_device_execution":1})
        wrong=dict(row,catalog_provider_match=False)
        self.assertEqual(summarize([dict(image,imports=[wrong])])["counts"],{"unknown":1})
        native=dict(row,native_export="present")
        self.assertEqual(summarize([dict(image,imports=[native])])["counts"],{"native_lookup_present":1})
    def test_independent_device_candidate_not_app_certified(self):
        row={"symbol":"_$s11Observation10ObservableMp","declared_provider":"/usr/lib/swift/libswiftObservation.dylib",
             "native_export":"unknown","status":"candidate_independent_device_tested",
             "catalog_provider_match":True,"weak":False}
        image={"path":"A","cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":[row]}
        self.assertEqual(summarize([image])["counts"],{"review_independent_device_tested_candidate":1})
        self.assertEqual(summarize([dict(image,cpu_subtype=2)])["counts"],{"architecture_unverified":1})
        self.assertEqual(summarize([dict(image,imports=[dict(row,catalog_provider_match=False)])])["counts"],{"unknown":1})
    def test_mixed_weak_library_and_strong_references(self):
        row={"symbol":"_x","declared_provider":"/usr/lib/test","native_export":"absent",
             "status":"unknown","catalog_provider_match":False,"weak":False,"library_weak":True}
        a={"path":"A","cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":[row]}
        self.assertEqual(summarize([a])["counts"],{"investigate_weak_absence":1})
        b=dict(a,path="B",imports=[dict(row,library_weak=False)])
        self.assertEqual(summarize([a,b])["counts"],{"investigate_required_absence":1})
    def test_lookup_scope_difference(self):
        row=dict(symbol="_x",declared_provider="/usr/lib/test",native_export="unknown",
                 status="missing_unresolved",catalog_provider_match=True,
                 native_lookup_pair={"first":"absent","tree":"present"})
        image=dict(path="A",cpu_type=0x100000c,cpu_subtype=0,complete=True,imports=[row])
        r=summarize([image])
        self.assertEqual(r["counts"],{"review_lookup_scope_difference":1})
        self.assertEqual(r["items"][0]["lookup_pairs"],[row["native_lookup_pair"]])
        row["native_lookup_pair"]={"first":"present","tree":"absent"}
        self.assertEqual(summarize([image])["counts"],{"conflicting_evidence":1})
        self.assertEqual(summarize([dict(image,cpu_subtype=2)])["counts"],{"architecture_unverified":1})
    def test_conflict_and_architecture(self):
        row={"symbol":"_x","declared_provider":"/usr/lib/test","native_export":"present",
             "status":"missing_unresolved","catalog_provider_match":True,"weak":False}
        a={"path":"A","cpu_type":0x100000c,"cpu_subtype":0,"complete":True,"imports":[row]}
        b=dict(a,path="B",cpu_subtype=2)
        r=summarize([a,b])
        self.assertEqual(r["counts"],{"conflicting_evidence":1,"architecture_unverified":1})

if __name__ == "__main__":
    unittest.main()
