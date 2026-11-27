import json,unittest,io,zipfile
from verify_observation import PIN,CATALOG,catalog_gate,verify,member,inspect

class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.pin=json.loads(PIN.read_text())
        self.catalog=json.loads(CATALOG.read_text())
    def test_catalog(self):
        self.assertEqual(catalog_gate(self.pin,self.catalog),9)
        self.catalog["symbols"][self.pin["required_symbols"][0]]["status"]="unknown"
        with self.assertRaisesRegex(ValueError,"catalog"):
            catalog_gate(self.pin,self.catalog)
    def test_reject_modified_artifact(self):
        with self.assertRaisesRegex(ValueError,"artifact digest"):
            verify(b"altered",self.pin,self.catalog)
    def test_reject_modified_library(self):
        with self.assertRaisesRegex(ValueError,"library digest"):
            inspect(b"altered",self.pin)
    def test_missing_member(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr("other","x")
        with zipfile.ZipFile(buf) as z:
            with self.assertRaisesRegex(ValueError,"missing or duplicate"):
                member(z,"expected")

if __name__=="__main__":
    unittest.main()
