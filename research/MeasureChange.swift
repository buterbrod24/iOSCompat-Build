import SwiftUI
import Foundation

@main struct Measure {
    static func main() {
        var count=0;var failed=0
        func check(_ name:String,_ ok:Bool) {
            count += 1
            if !ok { failed += 1 }
            print("\(ok ? "PASS" : "FAIL") \(name)")
        }
        var a=LegacyChangeState<Int>()
        check("no initial notification",a.receive(1,initial:false)==nil)
        let a2=a.receive(2,initial:false)
        check("old/new pair",a2?.0==1 && a2?.1==2)
        check("equal values suppressed",a.receive(2,initial:false)==nil)
        let a3=a.receive(1,initial:false)
        check("change back",a3?.0==2 && a3?.1==1)
        var b=LegacyChangeState<Int>()
        let b1=b.receive(7,initial:true)
        check("initial pair equal",b1?.0==7 && b1?.1==7)
        check("repeat appearance suppressed",b.receive(7,initial:true)==nil)
        var c=LegacyChangeState<Int?>()
        let c1=c.receive(nil,initial:true)
        check("optional initial nil",c1 != nil && c1!.0==nil && c1!.1==nil)
        let c2=c.receive(4,initial:false)
        check("nil to value",c2 != nil && c2!.0==nil && c2!.1==4)
        let c3=c.receive(nil,initial:false)
        check("value to nil",c3 != nil && c3!.0==4 && c3!.1==nil)
        check("equal nil suppressed",c.receive(nil,initial:false)==nil)
        print("TOTAL \(count-failed)/\(count)")
        if failed != 0 { exit(1) }
    }
}
