import Foundation
import SwiftUI

@MainActor
private final class Model:Observable {
    let registrar=ObservationRegistrar()
    private var raw=0
    var value:Int {
        get { registrar.access(self,keyPath:\.value);return raw }
        set { registrar.withMutation(of:self,keyPath:\.value) { raw=newValue } }
    }
}
private final class Other:Observable {}
@main struct Measure {
    @MainActor static func wait(_ predicate:()->Bool) async -> Bool {
        for _ in 0..<100 {
            if predicate() { return true }
            try? await Task.sleep(nanoseconds:5_000_000)
        }
        return predicate()
    }
    @MainActor static func main() async {
        let a=Model(),b=Model(),other=Other()
        let root=CompatObjectScope()
        let parent=root.setting(Model.self,a).setting(Other.self,other)
        let child=parent.setting(Model.self,b)
        let cleared=child.setting(Model.self,nil)
        var r:[(String,Bool)]=[]
        r.append(("missing object returns nil",root.object(Model.self)==nil))
        r.append(("parent model identity",parent.object(Model.self)===a))
        r.append(("child shadows same type",child.object(Model.self)===b))
        r.append(("parent unchanged",parent.object(Model.self)===a))
        r.append(("other type inherited",child.object(Other.self)===other))
        r.append(("explicit removal",cleared.object(Model.self)==nil && child.object(Model.self)===b))
        r.append(("unrelated type preserved on removal",cleared.object(Other.self)===other))
        let first=CompatTrackedValue { parent.object(Model.self)!.value }
        let second=CompatTrackedValue { child.object(Model.self)!.value }
        a.value=3
        let changed=await wait { first.value==3 }
        r.append(("parent projection independent",changed && second.value==0))
        b.value=5
        let changed2=await wait { second.value==5 }
        r.append(("child projection independent",changed2 && first.value==3))
        first.stop()
        a.value=7
        try? await Task.sleep(nanoseconds:30_000_000)
        r.append(("stopped parent does not publish",first.value==3))
        let demo=CompatEnvironmentProjection(Model.self,path:\.value) { Text(String($0)) } missing: { Text("Missing") }
            .compatEnvironment(Model.self,a)
        withExtendedLifetime(demo) {}
        for (n,ok) in r { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(r.filter{$0.1}.count)/10")
        if r.count != 10 || r.contains(where:{!$0.1}) { exit(1) }
    }
}
