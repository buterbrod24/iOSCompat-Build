public protocol FixtureProtocol { var number:Int { get } }
public struct PlainValue:FixtureProtocol {
    public var number:Int
    public init(_ value:Int) { number=value }
}
public struct GenericValue<T> {
    public let value:T
    public init(_ value:T) { self.value=value }
}
extension GenericValue:FixtureProtocol where T:Equatable {
    public var number:Int { value==value ? 1 : 0 }
}
public func consume<T:FixtureProtocol>(_ value:T)->Int { value.number }
