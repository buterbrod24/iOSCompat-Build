@inline(never)
public func stockReserve(_ array: inout ContiguousArray<AnyObject>, _ minimumCapacity:Int) {
    array.reserveCapacity(minimumCapacity)
}
