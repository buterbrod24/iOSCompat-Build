public struct Pair<T:Equatable,U> {
    public var first:T
    public var second:U
    public init(_ first:T,_ second:U) { self.first=first;self.second=second }
}
public enum GenericChoice<T:Hashable> { case value(T), empty }
