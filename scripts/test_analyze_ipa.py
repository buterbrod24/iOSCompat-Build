import pathlib, tempfile, unittest, zipfile, struct, json
from analyze_ipa import scan, map_dependencies
from macho_imports import read_dependencies, declared_provider

class AnalyzerTest(unittest.TestCase):
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)/"fixture.ipa"
            # Thin empty Mach-O header: no imports and not complete.
            header = struct.pack("<8I", 0xfeedfacf, 0x100000c, 0, 2, 0, 0, 0, 0)
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("Payload/Test.app/Test", header)
                z.writestr("Payload/Test.app/Frameworks/Bad", b"\xcf\xfa\xed\xfe")
                z.writestr("Payload/Test.app/Fat", b"\xca\xfe\xba\xbe")
                z.writestr("Payload/Test.app/info.txt", "not a binary")
            catalog = {"target":"16.2", "symbols":{}}
            before = p.read_bytes()
            r = scan(p, catalog)
            self.assertEqual(len(r["images"]), 3)
            self.assertFalse(r["images"][0]["complete"])
            self.assertIn("error", r["images"][1])
            self.assertIn("error", r["images"][2])
            self.assertEqual(before, p.read_bytes())

    def test_dependency_ordinals_and_catalog(self):
        def command(kind, name, minimum):
            payload = name.encode() + b"\0"
            size = (minimum + len(payload) + 7) & ~7
            return struct.pack("<III",kind,size,minimum) + bytes(minimum-12) + payload + bytes(size-minimum-len(payload))
        provider = "/usr/lib/swift/libswiftCore.dylib"
        commands = command(0xc, provider, 24) + command(0x8000001c, "@loader_path", 12) + command(0x80000018, "@rpath/Other.dylib", 24)
        strings = b"\0_swift_conformsToProtocol2\0"
        symoff = 32 + len(commands) + 24
        commands += struct.pack("<6I",2,24,symoff,1,symoff+16,len(strings))
        header = struct.pack("<8I",0xfeedfacf,0x100000c,0,2,4,len(commands),0,0)
        data = header + commands + struct.pack("<IBBHQ",1,1,0,0x100,0) + strings
        deps, rpaths = read_dependencies(data)
        self.assertEqual(rpaths, ["@loader_path"])
        self.assertEqual(declared_provider(deps,1,"nlist"), provider)
        self.assertEqual(declared_provider(deps,2,"nlist"), "@rpath/Other.dylib")
        self.assertIsNone(declared_provider(deps,255,"nlist"))
        self.assertIsNone(declared_provider(deps,255,"chained"))
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)/"fixture.ipa"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("Payload/Test.app/Test",data)
            catalog = {"target":"16.2","symbols":{"swift_conformsToProtocol2":{"provider":provider,"status":"missing_unresolved"}}}
            row = scan(p,catalog)["images"][0]["imports"][0]
            self.assertEqual(row["status"],"missing_unresolved")
            catalog["symbols"]["swift_conformsToProtocol2"]["provider"] = "/wrong"
            self.assertEqual(scan(p,catalog)["images"][0]["imports"][0]["status"],"unknown")

    def test_local_dependency_candidates(self):
        image = {"path":"Payload/Test.app/Test","rpaths":["@loader_path/Frameworks","@executable_path/Frameworks"],"dependencies":[
            {"path":"@rpath/A.dylib"},{"path":"@loader_path/Frameworks/B.dylib"},
            {"path":"@executable_path/Frameworks/A.dylib"},{"path":"/usr/lib/libSystem.B.dylib"},
            {"path":"@loader_path/../../Outside.dylib"}]}
        images = [image, {"path":"Payload/Test.app/Frameworks/A.dylib"},{"path":"Payload/Test.app/Frameworks/B.dylib"},{"path":"Outside.dylib"}]
        map_dependencies(images)
        deps = image["dependencies"]
        self.assertEqual(deps[0]["local_candidates"],["Payload/Test.app/Frameworks/A.dylib"])
        self.assertEqual(deps[1]["resolution"],"local_candidate")
        self.assertEqual(deps[2]["resolution"],"unresolved_context")
        self.assertEqual(deps[3]["resolution"],"system_unverified")
        self.assertEqual(deps[4]["local_candidates"],[])

if __name__ == "__main__":
    unittest.main()
