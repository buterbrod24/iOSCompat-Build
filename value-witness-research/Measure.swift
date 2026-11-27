import Foundation

private final class WeakSlot { weak var value:Reference? }
private struct LargeValue {
    var a:Int
    var b:Int
    var c:Int
    var d:Int
    var ref:Reference
}
@inline(never) private func copyLifetime(_ slot:WeakSlot)->Bool {
    let original=Reference(42)
    slot.value=original
    let copied=copyStorage(ValueBox(original))
    return copied.value === original && slot.value != nil
}
@inline(never) private func moveLifetime(_ slot:WeakSlot)->Bool {
    let original=Reference(43)
    slot.value=original
    let moved=roundtrip(ValueChoice.first(original))
    if case .first(let ref)=moved { return ref === original && slot.value != nil }
    return false
}
@inline(never) private func assignment(_ oldSlot:WeakSlot,_ newSlot:WeakSlot)->Bool {
    var target=ValueBox(Reference(1))
    oldSlot.value=target.value
    let replacement=Reference(2)
    newSlot.value=replacement
    replaceValue(&target,ValueBox(replacement))
    return target.value === replacement
}
@main struct Measure {
    static func main() {
        let c=WeakSlot(),m=WeakSlot(),old=WeakSlot(),new=WeakSlot()
        let cOK=copyLifetime(c)
        let mOK=moveLifetime(m)
        let aOK=assignment(old,new)
        let ref=Reference(9)
        let large=copyStorage(LargeValue(a:1,b:2,c:3,d:4,ref:ref))
        let enumValue=roundtrip(ValueChoice.second("second"))
        let enumOK:Bool
        if case .second(let value)=enumValue { enumOK=value=="second" } else { enumOK=false }
        let emptyOK:Bool
        if case .empty=copyStorage(ValueChoice<Int>.empty) { emptyOK=true } else { emptyOK=false }
        var original=ValueBox([1,2,3])
        let copy=copyValue(original)
        original.value.append(4)
        let rows:[(String,Bool)]=[
            ("generic integer storage copy",copyStorage(123)==123),
            ("generic string move",roundtrip(String(repeating:"x",count:128)).count==128),
            ("reference identity through copy",cOK),
            ("reference released after copy scope",c.value==nil),
            ("reference identity through enum move",mOK),
            ("reference released after move scope",m.value==nil),
            ("generic assignment identity",aOK),
            ("assignment releases both references after scope",old.value==nil && new.value==nil),
            ("large value storage copy",large.d==4 && large.ref===ref),
            ("payload enum case survives move",enumOK),
            ("empty enum case survives copy",emptyOK),
            ("copy-on-write value isolation",copy.value==[1,2,3] && original.value==[1,2,3,4])
        ]
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/12")
        if rows.contains(where:{!$0.1}) { exit(1) }
    }
}
