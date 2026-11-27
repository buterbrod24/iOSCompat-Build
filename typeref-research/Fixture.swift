public struct LocalValue {
    public var number:Int
    public init(number:Int) { self.number=number }
}
public struct GenericHolder<T> {
    public var value:T
    public var local:LocalValue
    public var list:[LocalValue]
    public init(value:T,local:LocalValue,list:[LocalValue]) {
        self.value=value;self.local=local;self.list=list
    }
}
public func reflectionControl(_ item:GenericHolder<Int>)->Int { item.local.number }
