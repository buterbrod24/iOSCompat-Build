import Foundation
enum UnifiedContextChecks {
    static func run() -> [(String, Bool)] {
        let a = contextValue(7)
        let b = contextValue("seven")
        let p = contextPair(a.item, b.item)
        let rows: [(String, Bool)] = [
            ("associated integer", contextItem(a) == 7),
            ("associated string", contextItem(b) == "seven"),
            ("distinct generic types", ObjectIdentifier(type(of: a)) != ObjectIdentifier(type(of: b))),
            ("conditional equality", p == contextPair(7, "seven")),
            ("conditional inequality", p != contextPair(8, "seven")),
            ("nested generic", contextItem(contextValue(a)).item == 7)
        ]
        return rows
    }
}
