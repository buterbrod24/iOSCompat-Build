import SwiftUI
import Darwin

@main struct Measure {
    @MainActor static func main() {
        var rows:[(String,Bool)]=[]
        let local:CompatLocalSpace = .local
        let global:CompatGlobalSpace = .global
        let named:CompatNamedSpace = .named("container")
        let other:CompatNamedSpace = .named(7)
        func isLocal<S:CompatCoordinateSpaceProtocol>(_ s:S)->Bool {
            if case .local=s.legacySpace { return true };return false
        }
        func isGlobal<S:CompatCoordinateSpaceProtocol>(_ s:S)->Bool {
            if case .global=s.legacySpace { return true };return false
        }
        func name<S:CompatCoordinateSpaceProtocol>(_ s:S)->AnyHashable? {
            if case .named(let value)=s.legacySpace { return value };return nil
        }
        rows.append(("local enum mapping",isLocal(local)))
        rows.append(("global enum mapping",isGlobal(global)))
        rows.append(("named string preserved",name(named)==AnyHashable("container")))
        rows.append(("non-string hashable preserved",name(other)==AnyHashable(7)))
        rows.append(("explicit scroll names distinct",name(CompatNamedSpace("outer")) != name(CompatNamedSpace("inner"))))
        let view=compatAssign(Text("Test"),named)
        let tapped=compatTap(view,local){_ in}
        let hosted=GeometryReader{ proxy in
            let _ = compatFrame(proxy,global)
            tapped
        }
        rows.append(("generic legacy view construction",type(of:hosted) != Never.self))
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/\(rows.count)")
        if rows.contains(where:{!$0.1}) { exit(1) }
    }
}
