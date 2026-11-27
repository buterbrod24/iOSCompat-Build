import Foundation
@main struct Measure {
    static func main() {
        let rows=MetadataChecks.run()
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/12")
        if rows.count != 12 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
