public protocol OpaqueValue {
    associatedtype Item
    var item:Item { get }
}
public struct Box<T>:OpaqueValue {
    public let item:T
    public init(_ item:T) { self.item=item }
}
public struct OtherBox<T>:OpaqueValue {
    public let item:T
    public init(_ item:T) { self.item=item }
}
@inline(never) public func first<T>(_ item:T)->some OpaqueValue { Box(item) }
@inline(never) public func second<T>(_ item:T)->some OpaqueValue { OtherBox(item) }
@inline(never) public func integer(_ item:Int)->some Equatable { item }
@inline(never) public func text(_ item:String)->some Equatable { item }
@inline(never) public func nested<T>(_ item:T)->some OpaqueValue { first(item) }
