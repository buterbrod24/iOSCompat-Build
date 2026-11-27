import Foundation
import Dispatch

public struct LookupBox<T> {}
public enum LookupChoice<T> { case value(T) }

@main struct MangledMeasure {
    static func main() {
        let types: [Any.Type] = [Int.self, String.self, Array<Int>.self,
            Dictionary<String, Int>.self, Optional<String>.self,
            LookupBox<Int>.self, LookupBox<String>.self, LookupChoice<Int>.self]
        var rows = types.enumerated().map { ("round trip \($0.offset)", MangledLookup.roundTrip($0.element)) }
        rows.append(("reject empty", MangledLookup.resolve("") == nil))
        rows.append(("reject control byte", MangledLookup.resolve("Si\u{0}") == nil))
        rows.append(("reject oversized", MangledLookup.resolve(String(repeating: "A", count: 4097)) == nil))
        rows.append(("distinct generic identities", ObjectIdentifier(LookupBox<Int>.self) != ObjectIdentifier(LookupBox<String>.self)))
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 12 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
