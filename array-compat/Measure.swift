import Foundation

private final class Token:NSObject {
    let n:Int
    init(_ n:Int){self.n=n}
}
@main struct Measure {
    static func main() {
        var count=0,passed=0
        func check(_ name:String,_ ok:Bool) {
            count += 1
            if ok { passed += 1 }
            print("\(ok ? "PASS" : "FAIL") \(name)")
        }
        let first=Token(1), second=Token(2)
        var empty=ContiguousArray<AnyObject>()
        empty.ioscompatReserveCapacity(0)
        check("empty zero",empty.isEmpty)
        empty.ioscompatReserveCapacity(128)
        check("empty reserve",empty.isEmpty && empty.capacity>=128)
        empty.append(first)
        check("append after reserve",empty.count==1 && empty[0]===first)
        var a:ContiguousArray<AnyObject>=[first,second]
        let original=a
        a.ioscompatReserveCapacity(64)
        check("shared reserve",a.count==2 && a.capacity>=64 && original.count==2)
        check("reference identity",a[0]===first && a[1]===second)
        a[0]=second
        check("copy on write",original[0]===first && a[0]===second)
        let oldCapacity=a.capacity
        a.ioscompatReserveCapacity(1)
        check("small reserve",a.capacity>=2 && a.count==2)
        a.ioscompatReserveCapacity(oldCapacity+100)
        check("growth reserve",a.capacity>=oldCapacity+100 && a[0]===second)
        weak var weakToken:Token?
        do {
            let item=Token(3)
            weakToken=item
            var lifetime:ContiguousArray<AnyObject>=[item]
            lifetime.ioscompatReserveCapacity(128)
            check("live reference",weakToken===item && lifetime[0]===item)
            withExtendedLifetime(lifetime){}
        }
        check("no leaked reference",weakToken==nil)
        print("TOTAL \(passed)/\(count)")
        if passed != count { exit(1) }
    }
}
