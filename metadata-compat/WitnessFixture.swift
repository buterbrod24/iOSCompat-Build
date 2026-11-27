// Original public protocol and conditional conformance fixture.
public protocol CompatReadable {
    var count: Int { get }
}
public struct WitnessBox<T> {
    public let value: T
    public init(_ value: T) { self.value = value }
}
extension WitnessBox: CompatReadable where T: Collection {
    public var count: Int { value.count }
}
@inline(never) public func witnessRead<T: CompatReadable>(_ value: T) -> Int {
    value.count
}
@inline(never) public func witnessCast(_ value: Any) -> Int? {
    (value as? any CompatReadable)?.count
}
