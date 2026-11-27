import SwiftUI
import Foundation

@main struct Measure {
    @MainActor static func main() {
        var light=EnvironmentValues()
        light.colorScheme = .light
        var dark=EnvironmentValues()
        dark.colorScheme = .dark
        var seen:[ColorScheme]=[]
        let adaptive=CompatStyleResolver { env in
            seen.append(env.colorScheme)
            return env.colorScheme == .dark ? Color.white : Color.black
        }
        let a=adaptive.resolve(in:light)
        let b=adaptive.resolve(in:dark)
        var r:[(String,Bool)]=[]
        r.append(("light and dark environment supplied",seen==[.light,.dark]))
        var changed=light
        changed.colorScheme = .dark
        _=adaptive.resolve(in:changed)
        r.append(("resolver reevaluated on each call",seen==[.light,.dark,.dark]))
        r.append(("source environment unchanged",light.colorScheme == .light))
        var contrast:[ColorSchemeContrast]=[]
        let gradient=CompatStyleResolver { env in
            contrast.append(env.colorSchemeContrast)
            return LinearGradient(colors:[.red,.blue],startPoint:.leading,endPoint:.trailing)
        }
        _=gradient.resolve(in:light)
        r.append(("gradient resolver accepts environment",contrast==[light.colorSchemeContrast]))
        var scales:[CGFloat]=[]
        let scale=CompatStyleResolver { env in
            scales.append(env.displayScale)
            return Color.red
        }
        var e=EnvironmentValues()
        e.displayScale=2
        _=scale.resolve(in:e)
        e.displayScale=3
        _=scale.resolve(in:e)
        r.append(("display scale forwarded",scales==[2,3]))
        let text=Text("test").compatForegroundStyle(adaptive)
        let shape=CompatFilledShape(Circle(),style:gradient)
        withExtendedLifetime((a,b,text,shape)) {}
        // Construction alone is not rendering or color equality evidence.
        for (n,ok) in r { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(r.filter{$0.1}.count)/5")
        if r.count != 5 || r.contains(where:{!$0.1}) { exit(1) }
    }
}
