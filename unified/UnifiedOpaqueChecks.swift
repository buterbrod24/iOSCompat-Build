import Foundation
import OpaqueFixture

enum UnifiedOpaqueChecks {
    static func sameType<A,B>(_ a:A,_ b:B)->Bool {
        ObjectIdentifier(A.self)==ObjectIdentifier(B.self)
    }
    static func equal<E:Equatable>(_ a:E,_ b:E)->Bool { a==b }
    static func read<O:OpaqueValue>(_ value:O)->Any { value.item }
    static func run() -> [(String, Bool)] {
        let a=first(7), b=first(8), c=first("abc")
        let d=second(7), e=nested(7)
        let rows:[(String,Bool)]=[
            ("same declaration and specialization",sameType(a,b)),
            ("different specialization",!sameType(a,c)),
            ("different underlying nominal type",!sameType(a,d)),
            ("nested opaque value preserves concrete runtime type",sameType(a,e)),
            ("associated item through generic call",(read(a) as? Int)==7),
            ("associated string through generic call",(read(c) as? String)=="abc"),
            ("integer opaque equality",equal(integer(3),integer(3))),
            ("integer opaque inequality",!equal(integer(3),integer(4))),
            ("string opaque equality",equal(text("x"),text("x"))),
            ("different concrete opaque types",!sameType(integer(1),text("1")))
        ]
        return rows
    }
}
