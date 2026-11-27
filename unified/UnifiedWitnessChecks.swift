import Foundation
import WitnessFixture

enum UnifiedWitnessChecks {
    static func run() -> [(String, Bool)] {
        let a = WitnessBox([1, 2, 3])
        let b = WitnessBox("abc")
        let empty = WitnessBox([Int]())
        let values: [Any] = [a, b, WitnessBox(42), empty]
        let rows: [(String, Bool)] = [
            ("generic array", witnessRead(a) == 3),
            ("generic string", witnessRead(b) == 3),
            ("empty collection", witnessRead(empty) == 0),
            ("cross-module positive cast", witnessCast(a) == 3),
            ("cross-module negative cast", witnessCast(WitnessBox(42)) == nil),
            ("heterogeneous existential dispatch", values.map(witnessCast) == [3, 3, nil, 0]),
            ("client-side positive conformance", (a as Any) is any CompatReadable),
            ("client-side negative conformance", !((WitnessBox(42) as Any) is any CompatReadable))
        ]
        return rows
    }
}

@_cdecl("ioscompat_unified_witness_mask")
public func ioscompat_unified_witness_mask() -> Int32 {
    let rows = UnifiedWitnessChecks.run()
    guard rows.count == 8 else { return -1 }
    return rows.enumerated().reduce(Int32(0)) { mask, row in
        mask | (row.element.1 ? (Int32(1) << row.offset) : 0)
    }
}
