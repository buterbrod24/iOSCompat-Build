import Foundation
import Dispatch

public struct LookupBox<T> {}
public enum LookupChoice<T> { case value(T) }

enum UnifiedMangledChecks {
    static func run() -> [(String, Bool)] {
        let types: [Any.Type] = [Int.self, String.self, Array<Int>.self,
            Dictionary<String, Int>.self, Optional<String>.self,
            LookupBox<Int>.self, LookupBox<String>.self, LookupChoice<Int>.self]
        var rows = types.enumerated().map { ("round trip \($0.offset)", MangledLookup.roundTrip($0.element)) }
        rows.append(("reject empty", MangledLookup.resolve("") == nil))
        rows.append(("reject control byte", MangledLookup.resolve("Si\u{0}") == nil))
        rows.append(("reject oversized", MangledLookup.resolve(String(repeating: "A", count: 4097)) == nil))
        rows.append(("distinct generic identities", ObjectIdentifier(LookupBox<Int>.self) != ObjectIdentifier(LookupBox<String>.self)))
        return rows
    }
}
