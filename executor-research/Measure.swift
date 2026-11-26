import Foundation

@main struct ExecutorMeasure {
    static func main() async {
        let rows = await ExecutorChecks.run()
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 4 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
