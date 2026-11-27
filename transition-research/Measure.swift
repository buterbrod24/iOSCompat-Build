import SwiftUI
import Darwin

@main struct Measure {
    @MainActor static func main() {
        let cases:[(String,CompatTransition)]=[
            ("identity",.identity),("opacity",.opacity),
            ("move",.move(edge:.leading)),("offset",.offset(CGSize(width:8,height:16))),
            ("combined",.opacity.combined(with:.move(edge:.bottom))),
            ("animated",.opacity.animation(.easeInOut(duration:0.2))),
            ("nil animation",.opacity.animation(nil)),
            ("asymmetric",.asymmetric(insertion:.opacity,removal:.move(edge:.trailing)))
        ]
        for (name,t) in cases {
            let view=Text("Sample").compatTransition(t)
            withExtendedLifetime(view) { print("CONSTRUCTED \(name)") }
        }
        print("TOTAL CONSTRUCTED \(cases.count)/8")
        // Construction smoke tests only: no rendered frame or timing comparison.
        if cases.count != 8 { exit(1) }
    }
}
