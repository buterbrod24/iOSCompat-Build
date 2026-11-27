public struct PlainValue {
    public var value:Int
    public init(_ value:Int) { self.value=value }
}
public struct GenericValue<T> {
    public var value:T
    public init(_ value:T) { self.value=value }
}
public enum ExampleEnum { case one, two(Int) }
public final class ExampleClass {
    public var value:Int
    public init(_ value:Int) { self.value=value }
}
