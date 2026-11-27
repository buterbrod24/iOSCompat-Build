import struct,unittest
from deployment_metadata import inspect_deployment

def image(*commands,cpu=0x100000c,subtype=0):
    body=b"".join(commands)
    return struct.pack("<8I",0xfeedfacf,cpu,subtype,2,len(commands),len(body),0,0)+body

def build(platform=2,minimum=0x100200,sdk=0x120500):
    return struct.pack("<8I",0x32,32,platform,minimum,sdk,1,3,0x10000)

class DeploymentTests(unittest.TestCase):
    def test_minimum_and_sdk_separate(self):
        r=inspect_deployment(image(build()))
        self.assertEqual(r["status"],"declared_minimum_within_target")
        self.assertEqual(r["records"][0]["sdk"],[18,5,0])
        self.assertEqual(r["records"][0]["tools"],[{"tool":3,"version":[1,0,0]}])
    def test_newer_patch(self):
        self.assertEqual(inspect_deployment(image(build(minimum=0x100201)))["status"],"minimum_above_target")
    def test_platform(self):
        self.assertEqual(inspect_deployment(image(build(platform=7)))["status"],"non_ios_declaration")
        self.assertEqual(inspect_deployment(image(build(platform=6)))["status"],"non_ios_declaration")
    def test_legacy_and_missing(self):
        old=struct.pack("<4I",0x25,16,0x0c0000,0x0c0000)
        self.assertEqual(inspect_deployment(image(old))["status"],"declared_minimum_within_target")
        self.assertEqual(inspect_deployment(image())["status"],"metadata_missing")
    def test_ambiguous_and_arch(self):
        self.assertEqual(inspect_deployment(image(build(),build()))["status"],"multiple_declarations_unverified")
        self.assertEqual(inspect_deployment(image(build(),subtype=2))["status"],"architecture_unverified")
    def test_malformed(self):
        with self.assertRaises(ValueError):
            inspect_deployment(image(struct.pack("<6I",0x32,24,2,0x100200,0x120500,1)))
if __name__=="__main__":
    unittest.main()
