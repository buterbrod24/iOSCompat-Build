import unittest
from audit_contracts import extract

class Contracts(unittest.TestCase):
    def test_annotation(self):
        a="  @inlinable\n  internal func _endMutation() {\n    mutate()\n  }\n"
        b=a.replace("@inlinable","@_effects(notEscaping self.**)")
        self.assertNotEqual(extract(a,"_endMutation")[0],extract(b,"_endMutation")[0])
        self.assertEqual(extract(a,"_endMutation")[1:],extract(b,"_endMutation")[1:])
    def test_overload(self):
        a="  internal func _consumeAndCreateNew() -> X {\n    f()\n  }\n  internal func _consumeAndCreateNew(\n    bufferIsUnique: Bool\n  ) -> X {\n    g()\n  }\n"
        self.assertIn("g()",extract(a,"_consumeAndCreateNew")[2])
    def test_missing(self):
        with self.assertRaises(ValueError):
            extract("","_endMutation")
    def test_unclosed(self):
        with self.assertRaises(ValueError):
            extract("  internal func _endMutation() {\n","_endMutation")

if __name__=="__main__":
    unittest.main()
