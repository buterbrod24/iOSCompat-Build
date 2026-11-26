import Foundation
@main struct Measure {
    static func main(){
        // Native control only. The real-device suite will inject the separately
        // compiled SDK bridge from the signed candidate artifact.
        let control:ReserveProbe.Bridge = { raw,n in
            raw.assumingMemoryBound(to:ContiguousArray<AnyObject>.self).pointee.reserveCapacity(n)
        }
        let rows=ReserveProbe.run(control)
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter{$0.1}.count)/\(rows.count)")
        if rows.contains(where:{!$0.1}) {exit(1)}
    }
}
