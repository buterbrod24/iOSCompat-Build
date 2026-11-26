import Darwin

@main struct ObservationMeasure {
    static func main() {
        let rows = ObservationChecks.run()
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 8 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
