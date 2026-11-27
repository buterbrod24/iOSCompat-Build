import Foundation
@main struct Measure {
    static func main() {
        let rows = ArrayOwnershipChecks.run()
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 12 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
