public struct ValueBox<T> {
    public var value:T
    public init(_ value:T) { self.value=value }
}
public enum ValueChoice<T> { case empty, first(T), second(T) }
public final class Reference {
    public let number:Int
    public init(_ number:Int) { self.number=number }
}
@inline(never) public func copyValue<T>(_ value:T)->T { value }
@inline(never) public func replaceValue<T>(_ target:inout T,_ source:T) { target=source }
@inline(never) public func roundtrip<T>(_ value:T)->T {
    let source=UnsafeMutablePointer<T>.allocate(capacity:1)
    let target=UnsafeMutablePointer<T>.allocate(capacity:1)
    source.initialize(to:value)
    target.moveInitialize(from:source,count:1)
    source.deallocate()
    let result=target.move()
    target.deallocate()
    return result
}
@inline(never) public func copyStorage<T>(_ value:T)->T {
    let source=UnsafeMutablePointer<T>.allocate(capacity:1)
    let target=UnsafeMutablePointer<T>.allocate(capacity:1)
    source.initialize(to:value)
    target.initialize(from:UnsafePointer(source),count:1)
    source.deinitialize(count:1)
    source.deallocate()
    let result=target.move()
    target.deallocate()
    return result
}
