import unittest
from compare_ir import signature, split_params

class ShapeTest(unittest.TestCase):
    def test_attrs_and_names(self):
        a='declare swiftcc void @"$test"(ptr noalias sret(%T) align 8, ptr swiftself, ptr swifterror)'
        b='define protected swiftcc void @"$test"(ptr noalias sret(%T) align 8 %0, ptr swiftself %1, ptr swifterror %2) {'
        self.assertEqual(signature(a,"$test","declare"),signature(b,"$test","define"))
        self.assertNotEqual(signature(a,"$test","declare"),signature(b.replace("swiftself",""),"$test","define"))
    def test_aggregate(self):
        self.assertEqual(split_params("{ i64, ptr }, ptr sret(%T)"),["{ i64, ptr }","ptr sret(%T)"])
    def test_missing(self):
        with self.assertRaises(ValueError):
            signature("","$test","declare")

if __name__ == "__main__":
    unittest.main()
