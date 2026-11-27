import Foundation
import WitnessFixture

@main struct WitnessMeasure {
    static func main() {
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
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 8 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
