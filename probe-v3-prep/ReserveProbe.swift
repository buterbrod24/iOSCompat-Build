import Foundation

// Test code for a native C bridge accepting an initialized, exclusively
// borrowed ContiguousArray<AnyObject>. No private buffer representation.
public enum ReserveProbe {
    public typealias Bridge = @convention(c) (UnsafeMutableRawPointer,Int)->Void
    private final class Token:NSObject {
        let n:Int
        init(_ n:Int){ self.n=n }
    }
    public static func run(_ bridge:Bridge)->[(String,Bool)] {
        var results:[(String,Bool)]=[]
        func check(_ name:String,_ ok:Bool){results.append((name,ok))}
        func reserve(_ a:inout ContiguousArray<AnyObject>,_ n:Int){
            withUnsafeMutablePointer(to:&a) { bridge(UnsafeMutableRawPointer($0),n) }
        }
        let a=Token(1), b=Token(2)
        var empty=ContiguousArray<AnyObject>()
        reserve(&empty,0)
        check("empty zero",empty.isEmpty)
        reserve(&empty,128)
        check("empty reserve",empty.isEmpty && empty.capacity>=128)
        empty.append(a)
        check("append after reserve",empty.count==1 && empty[0]===a)
        var shared:ContiguousArray<AnyObject>=[a,b]
        let original=shared
        reserve(&shared,64)
        check("shared reserve",shared.count==2 && shared.capacity>=64 && original.count==2)
        check("identity",shared[0]===a && shared[1]===b)
        shared[0]=b
        check("copy on write",original[0]===a && shared[0]===b)
        reserve(&shared,1)
        check("smaller request",shared.capacity>=2 && shared.count==2)
        let cap=shared.capacity
        reserve(&shared,cap+100)
        check("growth",shared.capacity>=cap+100 && shared[0]===b)
        weak var weakToken:Token?
        do {
            let item=Token(3)
            weakToken=item
            var lifetime:ContiguousArray<AnyObject>=[item]
            reserve(&lifetime,128)
            check("live reference",weakToken===item && lifetime[0]===item)
            withExtendedLifetime(lifetime){}
        }
        check("reference released",weakToken==nil)
        var many=ContiguousArray<AnyObject>()
        for i in 0..<32 {
            reserve(&many,i+1)
            many.append(Token(i))
        }
        check("repeated growth",many.count==32 && many.enumerated().allSatisfy{($0.element as? Token)?.n==$0.offset})
        var snapshot=many
        reserve(&snapshot,512)
        snapshot.removeLast()
        check("snapshot intact",many.count==32 && snapshot.count==31 && (many.last as? Token)?.n==31)
        return results
    }
}
