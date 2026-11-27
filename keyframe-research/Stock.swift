import SwiftUI
import Foundation

@main struct StockComparison {
    @MainActor static func main() {
        guard #available(macOS 14.0, *) else { exit(1) }
        let native=KeyframeTimeline(initialValue:0.0) {
            LinearKeyframe(2.0,duration:1)
            LinearKeyframe(4.0,duration:1)
        }
        let local=CompatScalarTimeline(initial:0,frames:[.linear(2,duration:1),.linear(4,duration:1)])!
        var passed=0
        for i in 0...8 {
            let time=Double(i)/4
            let observed=native.value(time:time)
            let candidate=local.value(at:time)!
            let ok=abs(observed-candidate)<1e-6
            print("\(ok ? "PASS" : "FAIL") linear t=\(time) native=\(observed) candidate=\(candidate)")
            if ok { passed+=1 }
        }
        print("NATIVE LINEAR MATCH \(passed)/9")
        if passed != 9 { exit(1) }
    }
}
