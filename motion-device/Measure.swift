import Foundation
@main struct Measure {
    static func main() {
        let r=PlaybackChecks.run()
        for (n,ok) in r { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(r.filter{$0.1}.count)/10")
        if r.count != 10 || r.contains(where:{!$0.1}) { exit(1) }
    }
}
