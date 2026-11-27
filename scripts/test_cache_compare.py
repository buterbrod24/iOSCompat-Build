import unittest
from cache_compare import compare

P="/usr/lib/test.dylib"
def regular(weak=False):
    return {"kind":"regular","flags":4 if weak else 0,"weak_definition":weak}
def snap(version,symbols,**kwargs):
    r={"status":"trie_inspected","install_name":P,"architecture":[0x100000c,2],"symbols":symbols,"reexport_libraries":[]}
    r.update(kwargs)
    return {"schema":1,"platform":2,"architecture":"arm64e","cache_uuid":str(version),"os_version":version,"providers":{P:r}}
class Compare(unittest.TestCase):
    def test_direct_and_changed(self):
        a=snap([16,2,0],{"_removed":regular(),"_weak":regular(),"_same":regular()})
        b=snap([17,0,0],{"_new":regular(),"_weak":regular(True),"_same":regular()})
        r=compare(a,b)["providers"][P]
        self.assertEqual(r["newer_only_entries"],["_new"])
        self.assertEqual(r["older_only_entries"],["_removed"])
        self.assertEqual(r["changed_entries"][0]["name"],"_weak")
        self.assertEqual(r["unchanged_entry_count"],1)
    def test_reexport_change(self):
        a=snap([16,2,0],{"_x":regular()},reexport_libraries=["/A"])
        b=snap([17,0,0],{"_x":{"kind":"reexport","flags":8,"weak_definition":False,"provider":"/B","import_name":"_y"}},reexport_libraries=["/B"])
        r=compare(a,b)["providers"][P]
        self.assertEqual(r["newer_reexport_declarations"],["/B"])
        self.assertEqual(r["changed_entries"][0]["newer"]["import_name"],"_y")
    def test_unavailable_not_empty(self):
        a=snap([16,2,0],{},status="trie_not_available")
        b=snap([17,0,0],{"_x":regular()})
        r=compare(a,b)["providers"][P]
        self.assertEqual(r["status"],"not_comparable")
        self.assertNotIn("newer_only_entries",r)
    def test_unselected(self):
        a=snap([16,2,0],{})
        a["providers"]={}
        self.assertEqual(compare(a,snap([17,0,0],{}))["providers"][P]["older_status"],"unselected")
    def test_architecture(self):
        a=snap([16,2,0],{})
        b=snap([17,0,0],{},architecture=[0x100000c,0])
        self.assertEqual(compare(a,b)["providers"][P]["status"],"image_architecture_mismatch")
        b["architecture"]="arm64"
        with self.assertRaises(ValueError): compare(a,b)
    def test_version_order(self):
        with self.assertRaises(ValueError): compare(snap([17,0,0],{}),snap([16,2,0],{}))
if __name__=="__main__":
    unittest.main()
