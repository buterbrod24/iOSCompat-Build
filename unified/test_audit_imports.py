import tempfile
import unittest
from pathlib import Path
from audit_imports import audit, blocked_symbols, dependencies, GATED, CLIENTS

class AuditTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(blocked_symbols("(undefined) external _swift_conformsToProtocol2 (from libswiftCore)"), ["swift_conformsToProtocol2"])
        self.assertEqual(blocked_symbols("_swift_conformsToProtocol _swift_conformsToProtocol20 _$s_swift_conformsToProtocol2"), [])
    def test_deps(self):
        self.assertEqual(dependencies("file:\n\t@rpath/libTest.dylib (compatibility version 0.0.0, current version 0.0.0)\n"), ["@rpath/libTest.dylib"])
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            names = GATED | {"old"+str(i) for i in range(9)}
            for name in names:
                (root / (name+".imports.txt")).write_text("")
                dep = "@rpath/"+CLIENTS[name] if name in CLIENTS else "/usr/lib/libSystem.B.dylib"
                (root / (name+".dependencies.txt")).write_text("image:\n\t"+dep+" (compatibility version 0.0.0)\n")
            self.assertEqual(audit(root)["errors"], [])
            (root / "old0.imports.txt").write_text("_swift_conformsToProtocol2")
            self.assertEqual(audit(root)["errors"], [])
            (root / "UnifiedProbe.imports.txt").write_text("_swift_conformsToProtocol2")
            self.assertTrue(audit(root)["errors"])
            (root / "UnifiedProbe.imports.txt").write_text("")
            (root / "UnifiedProbe.dependencies.txt").write_text("image:\n\t@rpath/libWitnessFixture.dylib (compatibility version 0.0.0)\n")
            self.assertTrue(audit(root)["errors"])
            (root / "UnifiedProbe.imports.txt").unlink()
            self.assertTrue(audit(root)["errors"])

if __name__ == "__main__":
    unittest.main()
