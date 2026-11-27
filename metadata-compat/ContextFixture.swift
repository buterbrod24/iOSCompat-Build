// Original compiler fixture: contextual generic references and conditional conformances.
public protocol ContextReadable {
    associatedtype Item
    var item: Item { get }
}
public struct ContextBox<T>: ContextReadable {
    public let item: T
    public init(_ item: T) { self.item = item }
}
public struct ContextPair<A, B> {
    public let first: A
    public let second: B
    public init(_ first: A, _ second: B) { self.first = first; self.second = second }
}
extension ContextPair: Equatable where A: Equatable, B: Equatable {}
@inline(never) public func contextValue<T>(_ value: T) -> ContextBox<T> { ContextBox(value) }
@inline(never) public func contextItem<T: ContextReadable>(_ value: T) -> T.Item { value.item }
@inline(never) public func contextPair<A, B>(_ a: A, _ b: B) -> ContextPair<A, B> { ContextPair(a, b) }
