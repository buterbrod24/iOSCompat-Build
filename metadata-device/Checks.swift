import Foundation
import Dispatch

private struct CacheBox<T> { let value:T }
private struct CachePair<A,B> { let first:A; let second:B }
private indirect enum RecursiveValue<T> { case end(T), next(RecursiveValue<T>) }
private protocol CacheReadable { var count:Int { get } }
extension CacheBox:CacheReadable where T:Collection {
    var count:Int { value.count }
}
private final class IdentityStore {
    private let lock=NSLock()
    private var values:[Int:Set<ObjectIdentifier>]=[:]
    func insert(_ id:ObjectIdentifier,group:Int) {
        lock.lock(); defer { lock.unlock() }
        values[group,default:[]].insert(id)
    }
    func snapshot()->[Int:Set<ObjectIdentifier>] {
        lock.lock();defer { lock.unlock() }
        return values
    }
}
enum MetadataChecks {
    @inline(never) private static func identity<T>(_ type:T.Type)->ObjectIdentifier {
        ObjectIdentifier(CacheBox<T>.self)
    }
    @inline(never) private static func pair<A,B>(_ a:A.Type,_ b:B.Type)->ObjectIdentifier {
        ObjectIdentifier(CachePair<A,B>.self)
    }
    @inline(never) private static func read<T>(_ value:T)->Int? {
        (value as? any CacheReadable)?.count
    }
    static func run()->[(String,Bool)] {
        let store=IdentityStore()
        DispatchQueue.concurrentPerform(iterations:512) { i in
            let id:ObjectIdentifier
            switch i%4 {
            case 0:id=identity(Int.self)
            case 1:id=identity(String.self)
            case 2:id=pair(Int.self,String.self)
            default:id=pair(String.self,Int.self)
            }
            store.insert(id,group:i%4)
        }
        let groups=store.snapshot()
        let all=Set(groups.values.flatMap{$0})
        let node:RecursiveValue<Int> = .next(.next(.end(7)))
        func evaluate(_ node:RecursiveValue<Int>)->Int {
            switch node {
            case .end(let value):return value
            case .next(let child):return 1+evaluate(child)
            }
        }
        let array=CacheBox(value:[1,2,3])
        let string=CacheBox(value:"abc")
        let nested=CacheBox(value:CacheBox(value:5))
        let rows:[(String,Bool)]=[
            ("four specialization groups observed",groups.count==4),
            ("stable identities across concurrent requests",groups.values.allSatisfy{$0.count==1}),
            ("distinct specializations and argument ordering",all.count==4),
            ("identity stable after concurrent access",groups[0]==Set([identity(Int.self)])),
            ("pair identity stable",groups[2]==Set([pair(Int.self,String.self)])),
            ("nested generic stored value",nested.value.value==5),
            ("recursive generic value",evaluate(node)==9),
            ("recursive layout has positive size",MemoryLayout<RecursiveValue<Int>>.size>0),
            ("conditional collection conformance",read(array)==3),
            ("conditional string conformance",read(string)==3),
            ("nonconforming specialization rejected",read(CacheBox(value:42))==nil),
            ("distinct recursive specializations",ObjectIdentifier(RecursiveValue<Int>.self) != ObjectIdentifier(RecursiveValue<String>.self))
        ]
        return rows
    }
}
